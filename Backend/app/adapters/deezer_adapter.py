import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_DEEZER_SEARCH_URL = "https://api.deezer.com/search"
_MIN_DELAY_SECONDS = 0.2


class DeezerAdapter:
    """Implements IMetadataProvider using the Deezer API."""

    _semaphore = asyncio.Semaphore(5)

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(self, query: str, title: str) -> list[dict]:
        """Search Deezer for tracks matching the query string."""
        async with self._semaphore:
            await asyncio.sleep(_MIN_DELAY_SECONDS)
            try:
                logger.debug("Deezer search — query=%s", query)
                response = await self._client.get(
                    _DEEZER_SEARCH_URL,
                    params={"q": query, "limit": 10},
                    timeout=10.0,
                )

                if response.status_code == 429:
                    logger.warning("Deezer rate-limited — waiting 1s and retrying")
                    await asyncio.sleep(1.0)
                    response = await self._client.get(
                        _DEEZER_SEARCH_URL,
                        params={"q": query, "limit": 10},
                        timeout=10.0,
                    )

                response.raise_for_status()

            except httpx.TimeoutException:
                logger.warning("Deezer search timed out for query=%s", query)
                return []
            except httpx.ConnectError as exc:
                logger.warning("Deezer connection error: %s", exc)
                return []
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Deezer HTTP error %s for query=%s", exc.response.status_code, query
                )
                return []

        data = response.json().get("data", [])
        normalized = []
        for item in data:
            album = item.get("album", {})
            artist = item.get("artist", {})
            normalized.append(
                {
                    "title": item.get("title"),
                    "artist": artist.get("name"),
                    "album": album.get("title"),
                    "genre": None,  # Deezer /search does not return genre in basic results
                    "year": None,
                    "track_number": str(item.get("track_position", "")) or None,
                    "disc_number": str(item.get("disk_number", "")) or None,
                    "image_url": album.get("cover_xl") or album.get("cover_big"),
                    "source": "deezer",
                }
            )
        logger.debug("Deezer returned %d results for query=%s", len(normalized), query)
        return normalized
