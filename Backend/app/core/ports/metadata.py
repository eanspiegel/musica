from typing import Protocol


class IMetadataProvider(Protocol):
    async def search(self, query: str, title: str) -> list[dict]: ...
