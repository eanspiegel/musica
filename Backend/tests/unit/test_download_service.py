import pytest
from unittest.mock import AsyncMock

from app.services.download_service import DownloadService


@pytest.fixture
def mock_downloader() -> AsyncMock:
    """A mock implementing IDownloader using AsyncMock."""
    mock = AsyncMock()
    mock.fetch_info.return_value = {"title": "Test Video", "duration": 120}
    mock.get_qualities.return_value = {"formats": []}
    mock.download.return_value = "/tmp/test.mp3"
    return mock


@pytest.fixture
def download_service(mock_downloader: AsyncMock) -> DownloadService:
    return DownloadService(downloader=mock_downloader)


@pytest.mark.asyncio
async def test_analyze_url_returns_info_from_downloader(
    download_service: DownloadService,
    mock_downloader: AsyncMock,
) -> None:
    result = await download_service.analyze_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result == {"title": "Test Video", "duration": 120}
    mock_downloader.fetch_info.assert_called_once()


@pytest.mark.asyncio
async def test_create_job_returns_pending_job(download_service: DownloadService) -> None:
    job = await download_service.create_job(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        format_type="audio",
    )
    assert job.status == "pending"
    assert job.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert job.format_type == "audio"
    assert job.id is not None


@pytest.mark.asyncio
async def test_get_job_returns_none_for_unknown_id(download_service: DownloadService) -> None:
    result = await download_service.get_job("nonexistent-id-9999")
    assert result is None


@pytest.mark.asyncio
async def test_analyze_url_rejects_invalid_host(download_service: DownloadService) -> None:
    with pytest.raises(ValueError, match="Disallowed host"):
        await download_service.analyze_url("https://evil.com/watch?v=abc")


@pytest.mark.asyncio
async def test_analyze_url_rejects_invalid_scheme(download_service: DownloadService) -> None:
    with pytest.raises(ValueError, match="Disallowed URL scheme"):
        await download_service.analyze_url("ftp://www.youtube.com/watch?v=abc")
