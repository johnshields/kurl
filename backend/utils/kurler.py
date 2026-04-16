from dataclasses import dataclass

from clients.platforms import apple, deezer, spotify, tidal
from utils.logging import get_logger
from utils.url_parser import ParsedMusicUrl

logger = get_logger()

# Platforms that support direct ISRC/UPC lookup.
ISRC_PLATFORMS = {"spotify", "appleMusic", "deezer", "tidal"}


@dataclass
class KurlMatch:
    url: str
    title: str | None = None
    artist: str | None = None
    via: str = "isrc"  # isrc, upc, name


def _get_client(platform: str):
    """Return the client module for a platform, or None if unconfigured."""
    clients = {
        "spotify": spotify,
        "appleMusic": apple,
        "deezer": deezer,
        "tidal": tidal,
    }
    client = clients.get(platform)
    if client and client.is_configured():
        return client
    return None


async def _get_track_isrc(source: ParsedMusicUrl) -> tuple[str | None, str | None, str | None]:
    """Fetch ISRC + metadata from the source platform. Returns (isrc, title, artist)."""
    client = _get_client(source.platform)
    if not client:
        return None, None, None

    try:
        if source.platform == "appleMusic":
            track = await client.get_song(source.id, storefront=source.country or "us")
        else:
            track = await client.get_track(source.id)

        isrc = client.extract_isrc(track) if hasattr(client, "extract_isrc") else client.extract_track_isrc(track)
        title, artist = client.extract_metadata(track)
        logger.info("Source %s track %s -> ISRC=%s (%s - %s)", source.platform, source.id, isrc, artist, title)
        return isrc, title, artist
    except Exception as e:
        logger.warning("Failed to get ISRC from %s: %s", source.platform, e)
        return None, None, None


async def _search_track_by_isrc(target_platform: str, isrc: str, storefront: str | None = None) -> tuple[str | None, str | None, str | None]:
    """Search a target platform by ISRC. Returns (url, title, artist)."""
    client = _get_client(target_platform)
    if not client:
        return None, None, None

    try:
        if target_platform == "appleMusic":
            match = await client.search_by_isrc(isrc, storefront=storefront or "us")
        else:
            match = await client.search_by_isrc(isrc)

        if not match:
            return None, None, None

        if target_platform == "appleMusic":
            url = client.extract_song_url(match)
        else:
            url = client.extract_track_url(match)

        title, artist = client.extract_metadata(match)
        return url, title, artist
    except Exception as e:
        logger.warning("ISRC search on %s failed: %s", target_platform, e)
        return None, None, None


async def _get_album_upc(source: ParsedMusicUrl) -> tuple[str | None, str | None, str | None]:
    """Fetch UPC from the source platform album. Returns (upc, album_title, artist)."""
    client = _get_client(source.platform)
    if not client:
        return None, None, None

    try:
        if source.platform == "appleMusic":
            album = await client.get_album(source.id, storefront=source.country or "us")
        else:
            album = await client.get_album(source.id)

        if source.platform == "appleMusic":
            upc = client.extract_upc(album)
        else:
            upc = client.extract_album_upc(album) if hasattr(client, "extract_album_upc") else client.extract_upc(album)

        attrs = album.get("attributes", {}) if source.platform == "appleMusic" else album
        title = attrs.get("name") or attrs.get("title")
        artist = attrs.get("artistName") or attrs.get("artist", {}).get("name")
        logger.info("Source %s album %s -> UPC=%s", source.platform, source.id, upc)
        return upc, title, artist
    except Exception as e:
        logger.warning("Failed to get UPC from %s: %s", source.platform, e)
        return None, None, None


async def _search_album_by_upc(target_platform: str, upc: str, storefront: str | None = None) -> tuple[str | None, str | None, str | None]:
    """Search a target platform by UPC. Returns (url, title, artist)."""
    client = _get_client(target_platform)
    if not client:
        return None, None, None

    try:
        if target_platform == "appleMusic":
            match = await client.search_by_upc(upc, storefront=storefront or "us")
        else:
            match = await client.search_by_upc(upc)

        if not match:
            return None, None, None

        if target_platform == "appleMusic":
            url = client.extract_album_url(match)
        else:
            url = client.extract_album_url(match)

        attrs = match.get("attributes", {}) if target_platform == "appleMusic" else match
        title = attrs.get("name") or attrs.get("title")
        artist = attrs.get("artistName") or attrs.get("artist", {}).get("name")
        return url, title, artist
    except Exception as e:
        logger.warning("UPC search on %s failed: %s", target_platform, e)
        return None, None, None


async def kurl(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    """Resolve a parsed music URL to the target platform via ISRC/UPC/name.

    Returns a KurlMatch if successful, or None to signal the caller
    should fall back to Odesli.
    """
    # Only attempt direct resolution for platforms with API clients.
    if source.platform not in ISRC_PLATFORMS and target_platform not in ISRC_PLATFORMS:
        return None

    if source.entity_type == "track":
        return await _kurl_track(source, target_platform)

    if source.entity_type == "album":
        return await _kurl_album(source, target_platform)

    if source.entity_type == "artist":
        return await _kurl_artist(source, target_platform)

    return None


async def _kurl_track(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    isrc, title, artist = await _get_track_isrc(source)
    if not isrc:
        return None

    url, match_title, match_artist = await _search_track_by_isrc(target_platform, isrc)
    if not url:
        return None

    return KurlMatch(
        url=url,
        title=match_title or title,
        artist=match_artist or artist,
        via="isrc",
    )


async def _kurl_album(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    upc, title, artist = await _get_album_upc(source)
    if not upc:
        return None

    url, match_title, match_artist = await _search_album_by_upc(target_platform, upc)
    if not url:
        return None

    return KurlMatch(
        url=url,
        title=match_title or title,
        artist=match_artist or artist,
        via="upc",
    )


async def _kurl_artist(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    """Artist matching by name -- lower confidence than ISRC/UPC."""
    source_client = _get_client(source.platform)
    if not source_client:
        return None

    try:
        if source.platform == "appleMusic":
            artist_data = await source_client.get_artist(source.id, storefront=source.country or "us")
            name = artist_data.get("attributes", {}).get("name")
        else:
            artist_data = await source_client.get_artist(source.id)
            name = artist_data.get("name")

        if not name:
            return None
    except Exception as e:
        logger.warning("Failed to get artist name from %s: %s", source.platform, e)
        return None

    target_client = _get_client(target_platform)
    if not target_client:
        return None

    try:
        match = await target_client.search_artist(name)
        if not match:
            return None

        if target_platform == "appleMusic":
            url = target_client.extract_artist_url(match)
        else:
            url = target_client.extract_artist_url(match)

        if not url:
            return None

        return KurlMatch(url=url, title=name, via="name")
    except Exception as e:
        logger.warning("Artist search on %s failed: %s", target_platform, e)
        return None
