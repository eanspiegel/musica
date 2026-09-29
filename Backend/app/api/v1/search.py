import logging

from fastapi import APIRouter

from app.api.deps import MetadataServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metadata")
async def search_metadata(
    title: str,
    artist: str,
    service: MetadataServiceDep,
) -> list[dict]:
    query = f"{artist} {title}"
    return await service.itunes.search(query=query, title=title)
