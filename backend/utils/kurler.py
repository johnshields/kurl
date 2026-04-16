from dataclasses import dataclass

from app.constants import DEFAULT_STOREFRONT
from clients import metadata
from clients.platforms import apple, deezer, spotify, tidal
from utils.canonical_url import build_track_url
from utils.logging import get_logger
from utils.url_parser import ParsedMusicUrl, ParsedTrack

logger = get_logger()

# Platforms that support direct ISRC/UPC lookup.
ISRC_PLATFORMS = {"spotify", "appleMusic", "deezer", "tidal"}

_CLIENTS = {
    "spotify": spotify,
    "appleMusic": apple,
    "deezer": deezer,
    "tidal": tidal,
}


@dataclass
class KurlMatch:
    url: str
    title: str | None = None
    artist: str | None = None
    via: str = "isrc"  # isrc, upc, name, search_api


def _get_client(platform: str):
    """Return the client module for a platform, or None if unconfigured."""
    client = _CLIENTS.get(platform)
    return client if client and client.is_configured() else None


def _ctx(platform: str, country: str | None = None) -> dict:
    """Platform-specific kwargs for client calls (currently just Apple storefront)."""
    if platform == "appleMusic":
        return {"storefront": country or DEFAULT_STOREFRONT}
    return {}


async def kurl(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    """Resolve a parsed music URL to the target platform via ISRC/UPC/name.

    Returns a KurlMatch if successful, or None to signal the caller
    should fall back to Odesli.
    """
    # Attempt if at least the target has a configured client.
    if not _get_client(target_platform):
        return None

    if source.entity_type == "track":
        return await _kurl_track(source, target_platform)

    if source.entity_type == "album":
        return await _kurl_album(source, target_platform)

    if source.entity_type == "artist":
        return await _kurl_artist(source, target_platform)

    return None


async def _kurl_track(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    # Try ISRC path first (source creds required).
    isrc, title, artist = await _lookup_identifier(
        source,
        fetch="get_track",
        extract="extract_isrc",
        label="ISRC",
    )
    if isrc:
        match = await _search_by_identifier(
            target_platform,
            isrc,
            search="search_by_isrc",
            url_getter="extract_track_url",
            via="isrc",
            hint_title=title,
            hint_artist=artist,
        )
        if match:
            return match

    # Fallback: scrape metadata from source, search target API by title + artist.
    if not title or not artist:
        scraped_title, scraped_artist = await metadata.fetch_metadata(
            ParsedTrack(source.platform, source.id),
            _build_source_url(source),
        )
        title = title or scraped_title
        artist = artist or scraped_artist

    if not title or not artist:
        return None

    return await _search_track_by_metadata(target_platform, title, artist)


async def _kurl_album(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    upc, title, artist = await _lookup_identifier(
        source,
        fetch="get_album",
        extract="extract_upc",
        metadata_fn="extract_album_metadata",
        label="UPC",
    )
    if not upc:
        return None

    return await _search_by_identifier(
        target_platform,
        upc,
        search="search_by_upc",
        url_getter="extract_album_url",
        via="upc",
        metadata_fn="extract_album_metadata",
        hint_title=title,
        hint_artist=artist,
    )


async def _kurl_artist(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
    """Artist matching by name -- lower confidence than ISRC/UPC."""
    source_client = _get_client(source.platform)
    if not source_client:
        return None

    try:
        artist_data = await source_client.get_artist(source.id, **_ctx(source.platform, source.country))
        name = source_client.extract_artist_name(artist_data)
    except Exception as e:
        logger.warning("Failed to get artist name from %s: %s", source.platform, e)
        return None

    if not name:
        return None

    target_client = _get_client(target_platform)
    if not target_client:
        return None

    try:
        match = await target_client.search_artist(name, **_ctx(target_platform))
        if not match:
            return None
        url = target_client.extract_artist_url(match)
        if not url:
            return None
        return KurlMatch(url=url, title=name, via="name")
    except Exception as e:
        logger.warning("Artist search on %s failed: %s", target_platform, e)
        return None


async def _lookup_identifier(
    source: ParsedMusicUrl,
    *,
    fetch: str,
    extract: str,
    label: str,
    metadata_fn: str = "extract_metadata",
) -> tuple[str | None, str | None, str | None]:
    """Fetch an identifier (ISRC/UPC) + metadata from the source platform.

    Returns (identifier, title, artist). Any can be None on failure.
    """
    client = _get_client(source.platform)
    if not client:
        return None, None, None

    try:
        entity = await getattr(client, fetch)(source.id, **_ctx(source.platform, source.country))
        identifier = getattr(client, extract)(entity)
        title, artist = getattr(client, metadata_fn)(entity)
        logger.info(
            "Source %s %s=%s id=%s (%s - %s)",
            source.platform,
            label,
            identifier,
            source.id,
            artist,
            title,
        )
        return identifier, title, artist
    except Exception as e:
        logger.warning("Failed to get %s from %s: %s", label, source.platform, e)
        return None, None, None


async def _search_by_identifier(
    target_platform: str,
    identifier: str,
    *,
    search: str,
    url_getter: str,
    via: str,
    metadata_fn: str = "extract_metadata",
    hint_title: str | None = None,
    hint_artist: str | None = None,
) -> KurlMatch | None:
    """Search the target platform by ISRC or UPC and build a KurlMatch."""
    client = _get_client(target_platform)
    if not client:
        return None

    try:
        match = await getattr(client, search)(identifier, **_ctx(target_platform))
        if not match:
            return None
        url = getattr(client, url_getter)(match)
        if not url:
            return None
        title, artist = getattr(client, metadata_fn)(match)
        return KurlMatch(
            url=url,
            title=title or hint_title,
            artist=artist or hint_artist,
            via=via,
        )
    except Exception as e:
        logger.warning("%s search on %s failed: %s", via.upper(), target_platform, e)
        return None


async def _search_track_by_metadata(
    target_platform: str,
    title: str,
    artist: str,
) -> KurlMatch | None:
    """Search a target platform by title + artist. Lower confidence than ISRC."""
    client = _get_client(target_platform)
    if not client or not hasattr(client, "search_track"):
        return None

    try:
        match = await client.search_track(title, artist, **_ctx(target_platform))
        if not match:
            return None
        url = client.extract_track_url(match)
        if not url:
            return None
        match_title, match_artist = client.extract_metadata(match)
        logger.info(
            "Metadata search on %s: %s - %s -> %s",
            target_platform,
            artist,
            title,
            url,
        )
        return KurlMatch(
            url=url,
            title=match_title or title,
            artist=match_artist or artist,
            via="search_api",
        )
    except Exception as e:
        logger.warning("Metadata search on %s failed: %s", target_platform, e)
        return None


def _build_source_url(source: ParsedMusicUrl) -> str:
    """Reconstruct a URL from a parsed source for metadata scraping."""
    return build_track_url(source.platform, source.id, source.country, source.album_id)
