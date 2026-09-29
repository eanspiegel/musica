import logging

from fastapi import APIRouter

from app.api.deps import DownloadServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/info")
async def get_info(url: str, service: DownloadServiceDep) -> dict:
    return await service.analyze_url(url)


@router.get("/qualities")
async def get_qualities(
    url: str,
    service: DownloadServiceDep,
    codec: str = "mp4",
) -> dict:
    return await service.get_qualities(url, codec)
