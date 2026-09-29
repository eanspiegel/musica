import logging
from typing import Optional

from app.core.models.track import Track
from app.core.ports.lyrics import ILyricsProvider
from app.core.ports.metadata import IMetadataProvider
from app.core.ports.recognition import IAudioRecognition
from app.core.ports.tag_writer import ITagWriter

logger = logging.getLogger(__name__)


class MetadataService:
    """Orchestrates recognition, metadata lookup, lyrics fetch, and tag writing.
    Only calls port interfaces — zero library imports.
    """

    def __init__(
        self,
        itunes: IMetadataProvider,
        deezer: IMetadataProvider,
        lyrics: ILyricsProvider,
        tag_writer: ITagWriter,
        recognition: IAudioRecognition,
    ) -> None:
        self.itunes = itunes
        self._deezer = deezer
        self._lyrics = lyrics
        self._tag_writer = tag_writer
        self._recognition = recognition

    async def tag_file(
        self,
        file_path: str,
        artist_hint: Optional[str] = None,
        title_hint: Optional[str] = None,
    ) -> Optional[Track]:
        """Recognize, enrich, and tag an audio file. Returns the applied Track or None."""
        title: Optional[str] = title_hint
        artist: Optional[str] = artist_hint

        # Step 1 — Audio recognition
        recognition_result = await self._recognition.recognize(file_path)
        if recognition_result:
            title = recognition_result.get("title") or title
            artist = recognition_result.get("artist") or artist
            logger.info("Recognition OK — title=%s artist=%s", title, artist)

        if not title and not artist:
            logger.warning("tag_file: no title/artist from recognition or hints for %s", file_path)
            return None

        query = f"{artist or ''} {title or ''}".strip()

        # Step 2 — iTunes search
        track_data: Optional[dict] = None
        itunes_results = await self.itunes.search(query=query, title=title or "")
        if itunes_results:
            track_data = itunes_results[0]
            logger.debug("iTunes result used for %s", file_path)

        # Step 3 — Deezer fallback
        if not track_data:
            deezer_results = await self._deezer.search(query=query, title=title or "")
            if deezer_results:
                track_data = deezer_results[0]
                logger.debug("Deezer result used for %s", file_path)

        if not track_data:
            logger.warning("No metadata found for %s", file_path)
            return None

        track = Track(
            title=track_data.get("title") or title,
            artist=track_data.get("artist") or artist,
            album=track_data.get("album"),
            genre=track_data.get("genre"),
            year=track_data.get("year"),
            track_number=track_data.get("track_number"),
            disc_number=track_data.get("disc_number"),
            image_url=track_data.get("image_url"),
            lyrics=recognition_result.get("lyrics") if recognition_result else None,
        )

        # Step 4 — Lyrics fallback
        if not track.lyrics:
            lyrics_text = await self._lyrics.get_lyrics(
                title=track.title or "",
                artist=track.artist or "",
            )
            track = track.model_copy(update={"lyrics": lyrics_text})

        # Step 5 — Write tags
        await self._tag_writer.write(file_path, track)
        logger.info("Tags written to %s", file_path)

        return track
