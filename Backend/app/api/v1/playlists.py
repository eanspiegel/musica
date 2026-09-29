import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import PlaylistServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


class BatchDownloadRequest(BaseModel):
    url: str
    indices: list[int]
    format_type: str
    audio_format: str = "mp3"
    container: str = "mp4"


@router.post("/download")
async def batch_download(
    body: BatchDownloadRequest,
    service: PlaylistServiceDep,
) -> dict:
    items = [{"url": body.url, "index": i} for i in body.indices]
    results = await service.process_batch(
        items=items,
        format_type=body.format_type,
        audio_format=body.audio_format,
        directory="./downloads",
        container=body.container,
    )
    return {"message": "batch started", "count": len(results)}
