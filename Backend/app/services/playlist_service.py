import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.download_service import DownloadService
    from app.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)


class PlaylistService:
    """Orchestrates batch downloads with bounded concurrency."""

    def __init__(
        self,
        download_service: "DownloadService",
        metadata_service: "MetadataService",
        max_concurrent: int = 3,
    ) -> None:
        self._download_service = download_service
        self._metadata_service = metadata_service
        self._max_concurrent = max_concurrent

    async def process_batch(
        self,
        items: list[dict],
        format_type: str,
        audio_format: str,
        directory: str,
        container: str,
    ) -> list[dict]:
        """Download and tag multiple items concurrently, bounded by max_concurrent."""
        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def process_one(item: dict) -> dict:
            async with semaphore:
                url = item.get("url", "")
                try:
                    job = await self._download_service.create_job(
                        url=url,
                        format_type=format_type,
                        audio_format=audio_format,
                        codec=container,
                    )
                    result: dict = {"job_id": job.id, "url": url, "status": "started"}

                    if format_type == "audio" and job.file_path:
                        track = await self._metadata_service.tag_file(
                            file_path=job.file_path,
                        )
                        result["tagged"] = track is not None

                    return result
                except ValueError as exc:
                    logger.warning("Batch item skipped (ValueError): url=%s — %s", url, exc)
                    return {"url": url, "status": "error", "error": str(exc)}
                except Exception as exc:  # noqa: BLE001
                    logger.error("Batch item failed: url=%s — %s", url, exc)
                    return {"url": url, "status": "error", "error": str(exc)}

        tasks = [process_one(item) for item in items]
        results = await asyncio.gather(*tasks)
        return list(results)
