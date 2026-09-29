# Backend — FastAPI Architecture

> This document defines the structure, conventions, and mandatory patterns for the backend.  
> Every decision here is final until explicitly revised via a documented ADR.

---

## Stack

| Concern | Choice | Notes |
|---|---|---|
| Framework | **FastAPI** | Async-first, auto OpenAPI docs |
| Runtime | **Python 3.12+** | Minimum version |
| Package manager | **uv** | Fast, lockfile-based |
| Validation | **Pydantic v2** | Schemas + settings |
| Task queue | **asyncio** (built-in) | Upgradeable to Celery/ARQ if needed |
| Testing | **pytest + httpx** | Async test client |

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── settings.py              # Pydantic BaseSettings — all config from env
│   │
│   ├── api/                     # HTTP layer only — no business logic here
│   │   ├── v1/
│   │   │   ├── router.py        # Aggregates all v1 routers
│   │   │   ├── downloads.py     # /downloads endpoints
│   │   │   ├── metadata.py      # /metadata endpoints
│   │   │   ├── playlists.py     # /playlists endpoints
│   │   │   └── search.py        # /search endpoints
│   │   └── deps.py              # FastAPI dependency injection helpers
│   │
│   ├── core/                    # Pure domain logic — zero framework imports
│   │   ├── models/              # Pydantic domain models (not DB, not HTTP)
│   │   │   ├── track.py
│   │   │   ├── playlist.py
│   │   │   └── download_job.py
│   │   └── ports/               # Abstract interfaces (the "port" in Ports & Adapters)
│   │       ├── downloader.py    # IDownloader protocol
│   │       ├── metadata.py      # IMetadataProvider protocol
│   │       ├── lyrics.py        # ILyricsProvider protocol
│   │       └── recognition.py  # IAudioRecognition protocol
│   │
│   ├── adapters/                # Third-party integrations — one adapter per lib
│   │   ├── yt_dlp_adapter.py    # Implements IDownloader using yt-dlp
│   │   ├── shazam_adapter.py    # Implements IAudioRecognition using shazamio
│   │   ├── itunes_adapter.py    # Implements IMetadataProvider using iTunes API
│   │   ├── deezer_adapter.py    # Implements IMetadataProvider using Deezer API
│   │   ├── lrclib_adapter.py    # Implements ILyricsProvider using LRCLIB
│   │   └── mutagen_adapter.py   # Implements ITagWriter using mutagen
│   │
│   ├── services/                # Orchestration — calls ports, no HTTP, no lib imports
│   │   ├── download_service.py
│   │   ├── metadata_service.py
│   │   ├── playlist_service.py
│   │   └── recognition_service.py
│   │
│   └── infrastructure/
│       ├── container.py         # Dependency wiring (manual DI or dependency-injector)
│       └── file_manager.py      # Filesystem abstractions
│
├── tests/
│   ├── unit/                    # Test services/core with mocked ports
│   ├── integration/             # Test adapters against real libs (offline where possible)
│   └── e2e/                     # Full HTTP cycle with httpx
│
├── pyproject.toml
├── .env.example
└── Dockerfile
```

---

## Mandatory Patterns

### 1. Adapter Pattern (non-negotiable)

Every third-party library MUST be behind a **Port (abstract interface) + Adapter (concrete impl)**.

The goal: swapping yt-dlp for another downloader, or shazamio for another recognition service,
must require changing ONLY the adapter file — nothing in services or API layers.

**Port definition** (`core/ports/downloader.py`):
```python
from typing import Protocol, AsyncIterator
from app.core.models.download_job import DownloadJob, DownloadProgress

class IDownloader(Protocol):
    async def fetch_info(self, url: str) -> dict: ...
    async def download(
        self, job: DownloadJob, on_progress: AsyncIterator[DownloadProgress]
    ) -> str: ...
```

**Adapter** (`adapters/yt_dlp_adapter.py`):
```python
import yt_dlp
from app.core.ports.downloader import IDownloader

class YtDlpAdapter:
    """Concrete implementation of IDownloader using yt-dlp."""

    async def fetch_info(self, url: str) -> dict:
        # yt-dlp specifics contained here
        ...

    async def download(self, job, on_progress) -> str:
        # yt-dlp specifics contained here
        ...
```

**Service** (`services/download_service.py`):
```python
class DownloadService:
    def __init__(self, downloader: IDownloader):  # depends on PORT, not adapter
        self._downloader = downloader
```

### 2. API Layer — Thin Controllers

Routers handle ONLY:
- Request validation (Pydantic schemas)
- Calling the corresponding service
- Returning the response schema

**No business logic. No library imports. No file I/O.**

```python
@router.post("/downloads", response_model=DownloadJobResponse)
async def create_download(
    body: DownloadRequest,
    service: DownloadService = Depends(get_download_service),
):
    job = await service.create(body.url, body.format)
    return DownloadJobResponse.from_domain(job)
```

### 3. Settings via Pydantic BaseSettings

All configuration comes from environment variables. No hardcoded values anywhere.

```python
# app/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    download_path: str = "./downloads"
    max_concurrent_downloads: int = 3
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}
```

### 4. Dependency Injection via Container

All adapters are instantiated once in `infrastructure/container.py` and injected through
FastAPI's `Depends()`. No service instantiates its own dependencies.

---

## Third-Party Libraries → Adapter Mapping

| Library | Port Interface | Adapter File |
|---|---|---|
| `yt-dlp` | `IDownloader` | `yt_dlp_adapter.py` |
| `shazamio` | `IAudioRecognition` | `shazam_adapter.py` |
| `mutagen` | `ITagWriter` | `mutagen_adapter.py` |
| `requests` / iTunes API | `IMetadataProvider` | `itunes_adapter.py` |
| Deezer API | `IMetadataProvider` | `deezer_adapter.py` |
| LRCLIB API | `ILyricsProvider` | `lrclib_adapter.py` |

---

## API Conventions

- **Versioning**: All routes under `/api/v1/`
- **Response format**: JSON, snake_case keys
- **Errors**: RFC 7807 Problem Details (`{"type", "title", "status", "detail"}`)
- **CORS**: Allowed origins defined in `Settings.cors_origins`
- **OpenAPI**: Auto-generated at `/docs` (disabled in production via env flag)

---

## Environment Variables

```dotenv
# .env.example
DOWNLOAD_PATH=./downloads
MAX_CONCURRENT_DOWNLOADS=3
CORS_ORIGINS=["http://localhost:5173"]
OPENAPI_ENABLED=true
```

**Rule**: The `.env` file is NEVER committed. Only `.env.example` is versioned.

---

## Scalability Considerations

- Services are stateless — safe for horizontal scaling
- Progress callbacks in `IDownloader` are ready to become WebSocket / SSE streams without changing service logic
- The container wiring allows swapping local filesystem → S3 by only replacing the adapter
- If concurrency grows, `asyncio` queue can be replaced by Celery/ARQ by only modifying `infrastructure/`
- API versioning (`/v1/`) allows parallel versions with zero breaking changes for existing clients
