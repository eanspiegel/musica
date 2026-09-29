import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_LRCLIB_GET_URL = "https://lrclib.net/api/get"
_LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"


class LrclibAdapter:
    """Implements ILyricsProvider using the LRCLIB API."""

    _semaphore = asyncio.Semaphore(3)

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_lyrics(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> Optional[str]:
        """Fetch plain lyrics, falling back from /api/get to /api/search."""
        async with self._semaphore:
            # Primary: exact lookup
            lyrics = await self._try_get(title=title, artist=artist, album=album, duration=duration)
            if lyrics:
                return lyrics

            # Fallback: search endpoint
            lyrics = await self._try_search(title=title, artist=artist)
            return lyrics

    async def _try_get(
        self,
        title: str,
        artist: str,
        album: Optional[str],
        duration: Optional[int],
    ) -> Optional[str]:
        params: dict = {"track_name": title, "artist_name": artist}
        if album:
            params["album_name"] = album
        if duration is not None:
            params["duration"] = duration

        try:
            response = await self._client.get(_LRCLIB_GET_URL, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("plainLyrics")
        except httpx.TimeoutException:
            logger.warning("LRCLIB /get timed out for title=%s artist=%s", title, artist)
            return None
        except httpx.ConnectError as exc:
            logger.warning("LRCLIB /get connection error: %s", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("LRCLIB /get HTTP error %s", exc.response.status_code)
            return None

    async def _try_search(self, title: str, artist: str) -> Optional[str]:
        params = {"q": f"{artist} {title}"}
        try:
            response = await self._client.get(_LRCLIB_SEARCH_URL, params=params, timeout=10.0)
            response.raise_for_status()
            results = response.json()
            if not results:
                return None
            # Use the first result that has plainLyrics
            for item in results:
                lyrics = item.get("plainLyrics")
                if lyrics:
                    return lyrics
            return None
        except httpx.TimeoutException:
            logger.warning("LRCLIB /search timed out for title=%s artist=%s", title, artist)
            return None
        except httpx.ConnectError as exc:
            logger.warning("LRCLIB /search connection error: %s", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("LRCLIB /search HTTP error %s", exc.response.status_code)
            return None
