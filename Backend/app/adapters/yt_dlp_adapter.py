import asyncio
import logging
from typing import Callable, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
}


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
    import os
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
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None

        if format_type == "music":
            temp_path = ydl.prepare_filename(info)
            base, _ = os.path.splitext(temp_path)
            final_path = f"{base}.{audio_format}"
            if os.path.exists(final_path):
                return final_path
        else:
            final_path = ydl.prepare_filename(info)
            if os.path.exists(final_path):
                return final_path
            base, _ = os.path.splitext(final_path)
            path_merged = f"{base}.{container}"
            if os.path.exists(path_merged):
                return path_merged

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
        _validate_url(url)
        logger.debug("Fetching info: %s", url)
        return await asyncio.to_thread(_extract_info_sync, url)

    async def get_qualities(self, url: str, codec: str = "mp4") -> dict:
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
