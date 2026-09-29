from typing import Optional, Protocol


class IAudioRecognition(Protocol):
    async def recognize(self, file_path: str) -> Optional[dict]: ...
