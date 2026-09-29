import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
_MIN_DELAY_SECONDS = 0.2


class ItunesAdapter:
    """Implements IMetadataProvider using the iTunes Search API."""

    _semaphore = asyncio.Semaphore(5)

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(self, query: str, title: str) -> list[dict]:
        """Search iTunes for tracks matching the query string."""
        async with self._semaphore:
            await asyncio.sleep(_MIN_DELAY_SECONDS)
            try:
                logger.debug("iTunes search — query=%s", query)
                response = await self._client.get(
                    _ITUNES_SEARCH_URL,
                    params={"term": query, "media": "music", "limit": 10},
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("iTunes search timed out for query=%s", query)
                return []
            except httpx.ConnectError as exc:
                logger.warning("iTunes connection error: %s", exc)
                return []
            except httpx.HTTPStatusError as exc:
                logger.warning("iTunes HTTP error %s for query=%s", exc.response.status_code, query)
                return []

        results = response.json().get("results", [])
        normalized = []
        for item in results:
            if item.get("kind") != "song":
                continue
            normalized.append(
                {
                    "title": item.get("trackName"),
                    "artist": item.get("artistName"),
                    "album": item.get("collectionName"),
                    "genre": item.get("primaryGenreName"),
                    "year": (item.get("releaseDate") or "")[:4] or None,
                    "track_number": str(item.get("trackNumber", "")) or None,
                    "disc_number": str(item.get("discNumber", "")) or None,
                    "image_url": (item.get("artworkUrl100") or "").replace("100x100", "600x600"),
                    "source": "itunes",
                }
            )
        logger.debug("iTunes returned %d results for query=%s", len(normalized), query)
        return normalized
