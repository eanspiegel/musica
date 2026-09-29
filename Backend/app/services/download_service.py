import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse

from app.core.models.download_job import DownloadJob, DownloadProgress
from app.core.ports.downloader import IDownloader
from app.settings import get_settings

if TYPE_CHECKING:
    from app.services.metadata_service import MetadataService

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
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed URL scheme: '{parsed.scheme}'")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError(f"Disallowed host: '{parsed.hostname}'")


class DownloadService:
    """Orchestrates download lifecycle. Depends on IDownloader port — no library imports."""

    def __init__(self, downloader: IDownloader, metadata_service: Optional['MetadataService'] = None) -> None:
        self._downloader = downloader
        self._metadata_service = metadata_service
        self._jobs: dict[str, DownloadJob] = {}

    async def analyze_url(self, url: str) -> dict:
        _validate_url(url)
        logger.debug("analyze_url: %s", url)
        raw = await self._downloader.fetch_info(url)
        return self._normalize_info(raw, url)

    @staticmethod
    def _normalize_info(raw: dict, original_url: str) -> dict:
        """Map yt-dlp raw dict to the MediaInfo shape expected by the frontend."""
        raw_type = raw.get("_type", "video")
        is_playlist = raw_type == "playlist" or "entries" in raw

        # Format duration
        def fmt_duration(secs) -> str:
            if not secs:
                return "0:00"
            try:
                secs = int(secs)
            except (TypeError, ValueError):
                return str(secs)
            m, s = divmod(secs, 60)
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

        if is_playlist:
            entries = raw.get("entries") or []
            playlist_items = []
            for e in entries:
                if not e:
                    continue
                vid_id = e.get("id", "")
                thumb = e.get("thumbnail") or (
                    f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg" if vid_id else ""
                )
                vid_url = e.get("url") or e.get("webpage_url") or (
                    f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
                )
                playlist_items.append({
                    "title": e.get("title") or "Unknown",
                    "url": vid_url,
                    "uploader": e.get("uploader") or e.get("channel") or "Unknown",
                    "duration": fmt_duration(e.get("duration")),
                    "thumbnail": thumb,
                })

            return {
                "type": "playlist",
                "url": original_url,
                "title": raw.get("title") or "Playlist",
                "duration": f"{len(playlist_items)} videos",
                "uploader": raw.get("uploader") or raw.get("channel") or "Unknown",
                "thumbnail": raw.get("thumbnail") or (
                    playlist_items[0]["thumbnail"] if playlist_items else ""
                ),
                "playlist_items": playlist_items,
            }

        return {
            "type": "video",
            "url": original_url,
            "title": raw.get("title") or "Unknown",
            "duration": fmt_duration(raw.get("duration")),
            "uploader": raw.get("uploader") or raw.get("channel") or "Unknown",
            "thumbnail": raw.get("thumbnail") or "",
            "playlist_items": [],
        }

    async def get_qualities(self, url: str, codec: str) -> dict:
        _validate_url(url)
        return await self._downloader.get_qualities(url, codec)

    async def create_job(
        self,
        url: str,
        format_type: str,
        audio_format: str = "mp3",
        codec: str = "mp4",
        format_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> DownloadJob:
        _validate_url(url)
        settings = get_settings()
        job = DownloadJob(url=url, format_type=format_type)
        self._jobs[job.id] = job
        
        save_dir = directory if directory else settings.download_path
        
        logger.info("Created download job id=%s url=%s dir=%s", job.id, url, save_dir)
        asyncio.create_task(
            self._run_download(
                job_id=job.id,
                url=url,
                format_type=format_type,
                audio_format=audio_format,
                codec=codec,
                format_id=format_id,
                directory=save_dir,
            )
        )
        return job

    async def _run_download(
        self,
        job_id: str,
        url: str,
        format_type: str,
        audio_format: str,
        codec: str,
        format_id: Optional[str],
        directory: str,
    ) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            logger.error("_run_download: job %s not found", job_id)
            return

        job.status = "downloading"

        def on_progress(percent: float, eta: str) -> None:
            job.progress = percent
            logger.debug("Job %s progress: %.1f%% ETA: %s", job_id, percent, eta)

        try:
            file_path = await self._downloader.download(
                url=url,
                format_type=format_type,
                format_id=format_id,
                audio_format=audio_format,
                directory=directory,
                container=codec,
                on_progress=on_progress,
            )
            job.status = "done"
            job.progress = 100.0
            job.file_path = file_path

            if format_type == "music" and self._metadata_service:
                logger.info("Job %s: Tagging downloaded file...", job_id)
                await self._metadata_service.tag_file(file_path=file_path)

            logger.info("Job %s done — file=%s", job_id, file_path)
        except ValueError as exc:
            job.status = "failed"
            job.error = str(exc)
            logger.error("Job %s failed (ValueError): %s", job_id, exc)
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            logger.error("Job %s failed: %s", job_id, exc)

    async def get_job(self, job_id: str) -> Optional[DownloadJob]:
        return self._jobs.get(job_id)

    async def get_all_jobs(self) -> list[DownloadJob]:
        return list(self._jobs.values())

    async def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("cancel_job: job %s not found", job_id)
            return False
        job.status = "failed"
        job.error = "cancelled"
        logger.info("Job %s cancelled", job_id)
        return True
