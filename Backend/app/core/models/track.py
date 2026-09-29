from typing import Optional

from pydantic import BaseModel


class Track(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    track_number: Optional[str] = None
    disc_number: Optional[str] = None
    image_url: Optional[str] = None
    lyrics: Optional[str] = None
