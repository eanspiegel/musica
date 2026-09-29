import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ShazamAdapter:
    """Implements IAudioRecognition using shazamio (optional dependency)."""

    def __init__(self) -> None:
        try:
            import shazamio  # noqa: F401, PLC0415

            self._available = True
            logger.info("shazamio is available — ShazamAdapter ready")
        except ImportError:
            self._available = False
            logger.warning("shazamio not installed — ShazamAdapter will be unavailable")

    async def recognize(self, file_path: str) -> Optional[dict]:
        """Recognize audio from a local file and return normalized metadata."""
        if not self._available:
            logger.debug("ShazamAdapter skipped — shazamio not installed")
            return None

        try:
            from shazamio import Shazam  # noqa: PLC0415

            shazam = Shazam()
            logger.info("Recognizing file: %s", file_path)
            result = await shazam.recognize(file_path)

            track_data = result.get("track")
            if not track_data:
                logger.debug("No track recognized in: %s", file_path)
                return None

            metadata = result.get("tagaction", {}).get("metapages", [])
            sections = track_data.get("sections", [])

            # Extract lyrics from sections
            lyrics: Optional[str] = None
            for section in sections:
                if section.get("type") == "LYRICS":
                    text_parts = section.get("text", [])
                    if text_parts:
                        lyrics = "\n".join(text_parts)
                    break

            # Extract image from images dict
            images = track_data.get("images", {})
            image_url = images.get("coverarthq") or images.get("coverart")

            # Extract year from release date string
            release_date: Optional[str] = track_data.get("releasedate", "")
            year: Optional[str] = None
            if release_date and len(release_date) >= 4:
                year = release_date[:4]

            normalized = {
                "title": track_data.get("title"),
                "artist": track_data.get("subtitle"),
                "album": track_data.get("sections", [{}])[0].get("metadata", [{}])[0].get(
                    "text"
                )
                if sections
                else None,
                "genre": track_data.get("genres", {}).get("primary"),
                "year": year,
                "image_url": image_url,
                "lyrics": lyrics,
            }
            logger.info("Recognition successful — title=%s", normalized.get("title"))
            return normalized

        except Exception as exc:  # noqa: BLE001
            logger.error("ShazamAdapter.recognize failed: %s", exc)
            return None
