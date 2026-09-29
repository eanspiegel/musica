"""
Dependency container — wires adapters into services.

All singletons are lazily initialised on first call.
This avoids import-time side effects and keeps tests easy to override.
"""
from __future__ import annotations

import httpx

from app.adapters.deezer_adapter import DeezerAdapter
from app.adapters.itunes_adapter import ItunesAdapter
from app.adapters.lrclib_adapter import LrclibAdapter
from app.adapters.mutagen_adapter import MutagenAdapter
from app.adapters.shazam_adapter import ShazamAdapter
from app.adapters.yt_dlp_adapter import YtDlpAdapter
from app.services.download_service import DownloadService
from app.services.metadata_service import MetadataService
from app.services.playlist_service import PlaylistService
from app.services.recognition_service import RecognitionService
from app.settings import get_settings

# ---------------------------------------------------------------------------
# Shared HTTP client (one instance for all HTTP adapters)
# ---------------------------------------------------------------------------
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client  # noqa: PLW0603
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=15.0)
    return _http_client


# ---------------------------------------------------------------------------
# Adapter singletons
# ---------------------------------------------------------------------------
_yt_dlp_adapter: YtDlpAdapter | None = None
_shazam_adapter: ShazamAdapter | None = None
_itunes_adapter: ItunesAdapter | None = None
_deezer_adapter: DeezerAdapter | None = None
_lrclib_adapter: LrclibAdapter | None = None
_mutagen_adapter: MutagenAdapter | None = None


def _get_yt_dlp_adapter() -> YtDlpAdapter:
    global _yt_dlp_adapter  # noqa: PLW0603
    if _yt_dlp_adapter is None:
        _yt_dlp_adapter = YtDlpAdapter()
    return _yt_dlp_adapter


def _get_shazam_adapter() -> ShazamAdapter:
    global _shazam_adapter  # noqa: PLW0603
    if _shazam_adapter is None:
        _shazam_adapter = ShazamAdapter()
    return _shazam_adapter


def _get_itunes_adapter() -> ItunesAdapter:
    global _itunes_adapter  # noqa: PLW0603
    if _itunes_adapter is None:
        _itunes_adapter = ItunesAdapter(client=_get_http_client())
    return _itunes_adapter


def _get_deezer_adapter() -> DeezerAdapter:
    global _deezer_adapter  # noqa: PLW0603
    if _deezer_adapter is None:
        _deezer_adapter = DeezerAdapter(client=_get_http_client())
    return _deezer_adapter


def _get_lrclib_adapter() -> LrclibAdapter:
    global _lrclib_adapter  # noqa: PLW0603
    if _lrclib_adapter is None:
        _lrclib_adapter = LrclibAdapter(client=_get_http_client())
    return _lrclib_adapter


def _get_mutagen_adapter() -> MutagenAdapter:
    global _mutagen_adapter  # noqa: PLW0603
    if _mutagen_adapter is None:
        _mutagen_adapter = MutagenAdapter()
    return _mutagen_adapter


# ---------------------------------------------------------------------------
# Service singletons
# ---------------------------------------------------------------------------
_download_service: DownloadService | None = None
_metadata_service: MetadataService | None = None
_playlist_service: PlaylistService | None = None
_recognition_service: RecognitionService | None = None


def get_download_service() -> DownloadService:
    global _download_service  # noqa: PLW0603
    if _download_service is None:
        _download_service = DownloadService(
            downloader=_get_yt_dlp_adapter(),
            metadata_service=get_metadata_service(),
        )
    return _download_service


def get_metadata_service() -> MetadataService:
    global _metadata_service  # noqa: PLW0603
    if _metadata_service is None:
        _metadata_service = MetadataService(
            itunes=_get_itunes_adapter(),
            deezer=_get_deezer_adapter(),
            lyrics=_get_lrclib_adapter(),
            tag_writer=_get_mutagen_adapter(),
            recognition=_get_shazam_adapter(),
        )
    return _metadata_service


def get_playlist_service() -> PlaylistService:
    global _playlist_service  # noqa: PLW0603
    if _playlist_service is None:
        settings = get_settings()
        _playlist_service = PlaylistService(
            download_service=get_download_service(),
            metadata_service=get_metadata_service(),
            max_concurrent=settings.max_concurrent_downloads,
        )
    return _playlist_service


def get_recognition_service() -> RecognitionService:
    global _recognition_service  # noqa: PLW0603
    if _recognition_service is None:
        _recognition_service = RecognitionService(recognition=_get_shazam_adapter())
    return _recognition_service
