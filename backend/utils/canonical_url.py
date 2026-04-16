from app.constants import (
    ALBUM_URL_TEMPLATES,
    ARTIST_URL_TEMPLATES,
    DEFAULT_STOREFRONT,
    TRACK_URL_TEMPLATES,
    TRACK_WITH_ALBUM_URL_TEMPLATES,
)


def build_track_url(platform: str, track_id: str, country: str | None = None, album_id: str | None = None) -> str:
    """Build a canonical track URL for a platform."""
    if album_id and platform in TRACK_WITH_ALBUM_URL_TEMPLATES:
        template = TRACK_WITH_ALBUM_URL_TEMPLATES[platform]
    else:
        template = TRACK_URL_TEMPLATES.get(platform, "")
    if not template:
        return ""
    return template.format(
        id=track_id,
        country=country or DEFAULT_STOREFRONT,
        album_id=album_id or "",
    )


def build_album_url(platform: str, album_id: str, country: str | None = None) -> str:
    template = ALBUM_URL_TEMPLATES.get(platform, "")
    if not template:
        return ""
    return template.format(id=album_id, country=country or DEFAULT_STOREFRONT)


def build_artist_url(platform: str, artist_id: str, country: str | None = None) -> str:
    template = ARTIST_URL_TEMPLATES.get(platform, "")
    if not template:
        return ""
    return template.format(id=artist_id, country=country or DEFAULT_STOREFRONT)
