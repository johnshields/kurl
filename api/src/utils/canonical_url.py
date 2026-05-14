from app.constants import DEFAULT_STOREFRONT, URL_TEMPLATES


def _template(platform: str, kind: str) -> str:
    return URL_TEMPLATES.get(platform, {}).get(kind, "")


def build_track_url(platform: str, track_id: str, country: str | None = None, album_id: str | None = None) -> str:
    """Build a canonical track URL. Prefers track_in_album when album_id known."""
    template = _template(platform, "track_in_album") if album_id else ""
    if not template:
        template = _template(platform, "track")
    if not template:
        return ""
    return template.format(
        id=track_id,
        country=country or DEFAULT_STOREFRONT,
        album_id=album_id or "",
    )


def build_album_url(platform: str, album_id: str, country: str | None = None) -> str:
    template = _template(platform, "album")
    if not template:
        return ""
    return template.format(id=album_id, country=country or DEFAULT_STOREFRONT)


def build_artist_url(platform: str, artist_id: str, country: str | None = None) -> str:
    template = _template(platform, "artist")
    if not template:
        return ""
    return template.format(id=artist_id, country=country or DEFAULT_STOREFRONT)
