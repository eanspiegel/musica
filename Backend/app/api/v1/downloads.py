import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import DownloadServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


class DownloadRequest(BaseModel):
    url: str
    format_type: str
    audio_format: str = "mp3"
    codec: str = "mp4"
    format_id: Optional[str] = None
    directory: Optional[str] = None


class DownloadJobResponse(BaseModel):
    id: str
    url: str
    format_type: str
    status: str
    progress: float
    file_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


@router.post("/", response_model=DownloadJobResponse)
async def create_download(
    body: DownloadRequest,
    service: DownloadServiceDep,
) -> DownloadJobResponse:
    job = await service.create_job(
        url=body.url,
        format_type=body.format_type,
        audio_format=body.audio_format,
        codec=body.codec,
        format_id=body.format_id,
        directory=body.directory,
    )
    return DownloadJobResponse(**job.model_dump())


@router.get("/", response_model=list[DownloadJobResponse])
async def list_downloads(service: DownloadServiceDep) -> list[DownloadJobResponse]:
    jobs = await service.get_all_jobs()
    return [DownloadJobResponse(**j.model_dump()) for j in jobs]


@router.get("/{job_id}", response_model=DownloadJobResponse)
async def get_download(job_id: str, service: DownloadServiceDep) -> DownloadJobResponse:
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return DownloadJobResponse(**job.model_dump())


@router.delete("/{job_id}")
async def cancel_download(job_id: str, service: DownloadServiceDep) -> dict:
    await service.cancel_job(job_id)
    return {"message": "cancelled"}
