from typing import Protocol

from app.core.models.track import Track


class ITagWriter(Protocol):
    async def write(self, file_path: str, track: Track) -> None: ...
