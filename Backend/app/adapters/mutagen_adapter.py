import logging
from typing import Optional

import httpx

from app.core.models.track import Track

logger = logging.getLogger(__name__)


class MutagenAdapter:
    """Implements ITagWriter using mutagen (imported lazily inside the method)."""

    async def write(self, file_path: str, track: Track) -> None:
        """Write ID3/Opus tags to the given audio file."""
        import mutagen  # noqa: PLC0415

        suffix = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""

        if suffix == "mp3":
            await self._write_mp3(file_path, track)
        elif suffix == "opus":
            await self._write_opus(file_path, track)
        else:
            logger.warning("MutagenAdapter: unsupported format '%s' for %s", suffix, file_path)

    async def _write_mp3(self, file_path: str, track: Track) -> None:
        from mutagen.easyid3 import EasyID3  # noqa: PLC0415
        from mutagen.id3 import APIC, ID3, USLT, error as ID3Error  # noqa: PLC0415

        try:
            tags = EasyID3(file_path)
        except ID3Error:
            tags = EasyID3()
            tags.save(file_path)
            tags = EasyID3(file_path)

        if track.title:
            tags["title"] = [track.title]
        if track.artist:
            tags["artist"] = [track.artist]
        if track.album:
            tags["album"] = [track.album]
        if track.genre:
            tags["genre"] = [track.genre]
        if track.year:
            tags["date"] = [track.year]
        if track.track_number:
            tags["tracknumber"] = [track.track_number]
        if track.disc_number:
            tags["discnumber"] = [track.disc_number]
        tags.save()

        # Cover art and lyrics require raw ID3 access
        id3 = ID3(file_path)

        if track.image_url:
            image_data = await self._download_image(track.image_url)
            if image_data:
                id3.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime="image/jpeg",
                        type=3,  # Cover (front)
                        desc="Cover",
                        data=image_data,
                    )
                )

        if track.lyrics:
            id3.add(
                USLT(encoding=3, lang="eng", desc="", text=track.lyrics)
            )

        id3.save()
        logger.info("MP3 tags written to %s", file_path)

    async def _write_opus(self, file_path: str, track: Track) -> None:
        from mutagen.oggopus import OggOpus  # noqa: PLC0415

        audio = OggOpus(file_path)

        if track.title:
            audio["title"] = [track.title]
        if track.artist:
            audio["artist"] = [track.artist]
        if track.album:
            audio["album"] = [track.album]
        if track.genre:
            audio["genre"] = [track.genre]
        if track.year:
            audio["date"] = [track.year]
        if track.track_number:
            audio["tracknumber"] = [track.track_number]
        if track.disc_number:
            audio["discnumber"] = [track.disc_number]
        if track.lyrics:
            audio["lyrics"] = [track.lyrics]

        if track.image_url:
            image_data = await self._download_image(track.image_url)
            if image_data:
                from mutagen.flac import Picture  # noqa: PLC0415
                import base64  # noqa: PLC0415
                
                pic = Picture()
                pic.type = 3  # Cover (front)
                pic.mime = "image/jpeg"
                pic.desc = "Cover"
                pic.data = image_data
                
                pic_data = pic.write()
                encoded_data = base64.b64encode(pic_data).decode("ascii")
                audio["metadata_block_picture"] = [encoded_data]

        audio.save()
        logger.info("Opus tags written to %s", file_path)

    async def _download_image(self, url: str) -> Optional[bytes]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.TimeoutException:
            logger.warning("Cover art download timed out: %s", url)
            return None
        except httpx.ConnectError as exc:
            logger.warning("Cover art connection error: %s", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("Cover art HTTP error %s: %s", exc.response.status_code, url)
            return None
