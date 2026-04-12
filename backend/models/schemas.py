from pydantic import BaseModel, HttpUrl


PLATFORMS = {
    "spotify",
    "appleMusic",
    "youtubeMusic",
    "deezer",
    "tidal",
    "amazonMusic",
    "pandora",
}


class ResolveRequest(BaseModel):
    url: HttpUrl
    target_platform: str


class ResolveResponse(BaseModel):
    title: str | None = None
    artist: str | None = None
    resolved_url: str
    platform: str
    cached: bool
