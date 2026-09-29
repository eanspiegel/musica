from pydantic import BaseModel


class PlaylistItem(BaseModel):
    title: str
    url: str
    uploader: str
    duration: str
    thumbnail: str


class PlaylistInfo(BaseModel):
    type: str = "playlist"
    title: str
    duration: str
    uploader: str
    thumbnail: str
    items: list[PlaylistItem]
