from pydantic import BaseModel, HttpUrl


class KurlRequest(BaseModel):
    url: HttpUrl
    target_platform: str


class KurlResponse(BaseModel):
    title: str | None = None
    artist: str | None = None
    resolved_url: str
    platform: str
    cached: bool
