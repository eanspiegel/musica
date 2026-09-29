from fastapi import APIRouter

from app.api.v1 import downloads, metadata, playlists, search

router = APIRouter(prefix="/api/v1")

router.include_router(downloads.router, prefix="/downloads", tags=["downloads"])
router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
router.include_router(search.router, prefix="/search", tags=["search"])
