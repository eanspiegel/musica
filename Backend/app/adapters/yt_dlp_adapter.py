import asyncio
import glob
import logging
import os
import time
from typing import Callable, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
}

# Query params that identify YouTube radio/mix sessions — not real playlists.
# When these are present the URL should be treated as a plain video.
_RADIO_PARAMS = {"start_radio", "radio"}


def _clean_url(url: str) -> str:
    """Normalize a YouTube URL before handing it to yt-dlp.

    Rules:
    - Strip tracking/session params that add no meaning (si, pp, index, etc.).
    - If ``list`` starts with ``RD`` (radio/mix) or ``start_radio=1`` is present,
      remove both so the URL resolves as a plain video — radio queues are not
      real playlists and yt-dlp can't enumerate them reliably.
    - If ``list`` points to a real playlist (not a radio), rewrite the URL to
      ``/playlist?list=...`` so yt-dlp resolves the full playlist instead of
      the individual video referenced by ``v=``.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=False)

    # Detect radio/mix: list starts with "RD" or start_radio is set
    list_id = (qs.get("list") or [""])[0]
    is_radio = list_id.startswith("RD") or any(p in qs for p in _RADIO_PARAMS)

    # Params to always discard (tracking / session noise)
    _STRIP = {"si", "pp", "index", "t", "start_radio", "radio", "feature"}

    cleaned: dict[str, list[str]] = {}
    for key, values in qs.items():
        if key in _STRIP:
            continue
        if key == "list" and is_radio:
            # Drop the radio list entirely; keep only the video id
            continue
        cleaned[key] = values

    # Real playlist: rewrite to /playlist?list=... so yt-dlp has no ambiguity.
    # When v= and list= coexist, yt-dlp resolves the single video by default.
    has_real_playlist = bool(list_id) and not is_radio
    if has_real_playlist and parsed.path in ("/watch", "/watch/"):
        host = parsed.scheme + "://" + (parsed.hostname or "www.youtube.com")
        return f"{host}/playlist?list={list_id}"

    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _validate_url(url: str) -> None:
    """TD-03 fix: allowlist validation before passing any URL to yt-dlp."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed URL scheme: '{parsed.scheme}'.")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError(f"Disallowed host: '{parsed.hostname}'. Only YouTube URLs are supported.")


# ---------------------------------------------------------------------------
# Synchronous helpers — run inside asyncio.to_thread to avoid blocking the
# FastAPI event loop. yt-dlp is fully synchronous and has no async API.
# ---------------------------------------------------------------------------

def _extract_info_sync(url: str) -> dict:
    import yt_dlp  # noqa: PLC0415

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.sanitize_info(info) if info else {}


def _get_qualities_sync(url: str, codec: str) -> dict:
    import yt_dlp  # noqa: PLC0415

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            return {"formats": []}

        formats = info.get("formats", [])
        filtered = [
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution") or f.get("height"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize"),
                "tbr": f.get("tbr"),
                "format_note": f.get("format_note"),
            }
            for f in formats
            if codec.lower() in (f.get("ext", "") or "")
            or (codec.lower() == "mp4" and f.get("vcodec") not in (None, "none"))
        ]
        return {"formats": filtered, "title": info.get("title", "")}


def _download_sync(
    url: str,
    format_type: str,
    format_id: Optional[str],
    audio_format: str,
    directory: str,
    container: str,
    on_progress: Optional[Callable],
) -> Optional[str]:
    import yt_dlp  # noqa: PLC0415

    if not os.path.exists(directory):
        os.makedirs(directory)

    def progress_hook(d: dict) -> None:
        if d["status"] == "downloading":
            percent_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                percent = float(percent_str)
            except ValueError:
                percent = 0.0
            eta = d.get("_eta_str", "")
            if on_progress:
                on_progress(percent, eta)

    ydl_opts = {
        "outtmpl": f"{directory}/%(title)s.%(ext)s",
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
    }

    if format_type == "music":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "320",
            }
        ]
    else:
        fmt = format_id if format_id else f"bestvideo[ext={container}]+bestaudio/best"
        ydl_opts["format"] = fmt
        ydl_opts["merge_output_format"] = container

    logger.info("Starting download — url=%s format_type=%s", url, format_type)

    # Snapshot files before download to detect new files reliably
    before = set(glob.glob(os.path.join(directory, "*")))
    started_at = time.time()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None

    # Find the newest file added since we started — handles restrictfilenames
    # mangling and FFmpeg rename chains (e.g. .webm → .mp3)
    expected_ext = audio_format if format_type == "music" else container
    after = set(glob.glob(os.path.join(directory, "*")))
    new_files = [
        f for f in (after - before)
        if f.lower().endswith(f".{expected_ext.lower()}")
    ]

    if new_files:
        # Prefer the file modified most recently in case of ties
        return max(new_files, key=os.path.getmtime)

    # Fallback: look for any file newer than our start time with the right ext
    all_matches = [
        f for f in glob.glob(os.path.join(directory, f"*.{expected_ext}"))
        if os.path.getmtime(f) >= started_at
    ]
    if all_matches:
        return max(all_matches, key=os.path.getmtime)

    logger.warning("Could not locate output file in %s for ext=%s", directory, expected_ext)
    return None


# ---------------------------------------------------------------------------
# Adapter class — async interface, blocking work delegated to thread pool
# ---------------------------------------------------------------------------

class YtDlpAdapter:
    """Concrete implementation of IDownloader using yt-dlp.

    yt-dlp is synchronous. Every call is offloaded to asyncio.to_thread()
    so the FastAPI event loop is never blocked.
    """

    async def fetch_info(self, url: str) -> dict:
        url = _clean_url(url)
        _validate_url(url)
        logger.debug("Fetching info: %s", url)
        return await asyncio.to_thread(_extract_info_sync, url)

    async def get_qualities(self, url: str, codec: str = "mp4") -> dict:
        url = _clean_url(url)
        _validate_url(url)
        logger.debug("Getting qualities — url=%s codec=%s", url, codec)
        return await asyncio.to_thread(_get_qualities_sync, url, codec)

    async def download(
        self,
        url: str,
        format_type: str,
        format_id: Optional[str],
        audio_format: str,
        directory: str,
        container: str,
        on_progress: Optional[Callable] = None,
    ) -> Optional[str]:
        url = _clean_url(url)
        _validate_url(url)
        return await asyncio.to_thread(
            _download_sync,
            url,
            format_type,
            format_id,
            audio_format,
            directory,
            container,
            on_progress,
        )
