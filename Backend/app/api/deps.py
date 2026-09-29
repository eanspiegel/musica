from typing import Annotated

from fastapi import Depends

from app.infrastructure.container import (
    get_download_service,
    get_metadata_service,
    get_playlist_service,
    get_recognition_service,
)
from app.services.download_service import DownloadService
from app.services.metadata_service import MetadataService
from app.services.playlist_service import PlaylistService
from app.services.recognition_service import RecognitionService

DownloadServiceDep = Annotated[DownloadService, Depends(get_download_service)]
MetadataServiceDep = Annotated[MetadataService, Depends(get_metadata_service)]
PlaylistServiceDep = Annotated[PlaylistService, Depends(get_playlist_service)]
RecognitionServiceDep = Annotated[RecognitionService, Depends(get_recognition_service)]
