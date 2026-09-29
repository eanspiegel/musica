import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DownloadJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    format_type: str
    status: str = "pending"
    progress: float = 0.0
    file_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class DownloadProgress:
    job_id: str
    percent: float
    eta: str = ""
