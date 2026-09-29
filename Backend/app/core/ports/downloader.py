from typing import Callable, Optional, Protocol


class IDownloader(Protocol):
    async def fetch_info(self, url: str) -> dict: ...

    async def get_qualities(self, url: str, codec: str) -> dict: ...

    async def download(
        self,
        url: str,
        format_type: str,
        format_id: Optional[str],
        audio_format: str,
        directory: str,
        container: str,
        on_progress: Optional[Callable],
    ) -> Optional[str]: ...
