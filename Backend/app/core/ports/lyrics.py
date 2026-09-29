from typing import Optional, Protocol


class ILyricsProvider(Protocol):
    async def get_lyrics(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> Optional[str]: ...
