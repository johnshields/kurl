from dataclasses import dataclass

from clients import metadata
from clients.platforms import apple, deezer, spotify, tidal
from utils.logging import get_logger
from utils.url_parser import ParsedMusicUrl, ParsedTrack

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
    isrc, title, artist = await _get_track_isrc(source)
    if isrc:
        url, match_title, match_artist = await _search_track_by_isrc(target_platform, isrc)
        if url:
            return KurlMatch(
                url=url,
                title=match_title or title,
                artist=match_artist or artist,
                via="isrc",
            )

    # Fallback: scrape metadata from source, search target API by title + artist.
    if not title or not artist:
        parsed_track = ParsedTrack(source.platform, source.id)
        source_url = _build_source_url(source)
        scraped_title, scraped_artist = await metadata.fetch_metadata(parsed_track, source_url)
        title = title or scraped_title
        artist = artist or scraped_artist

    if not title or not artist:
        return None

    return await _search_track_by_metadata(target_platform, title, artist)


async def _search_track_by_metadata(target_platform: str, title: str, artist: str) -> KurlMatch | None:
    """Search a target platform by title + artist. Lower confidence than ISRC."""
    client = _get_client(target_platform)
    if not client or not hasattr(client, "search_track"):
        return None

    try:
        match = await client.search_track(title, artist)
        if not match:
            return None

        if target_platform == "appleMusic":
            url = client.extract_song_url(match)
        else:
            url = client.extract_track_url(match)

        if not url:
            return None

        match_title, match_artist = client.extract_metadata(match)
        logger.info("Metadata search on %s: %s - %s -> %s", target_platform, artist, title, url)
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
    if source.platform == "spotify":
        return f"https://open.spotify.com/track/{source.id}"
    if source.platform == "appleMusic":
        country = source.country or "us"
        if source.album_id:
            return f"https://music.apple.com/{country}/album/_/{source.album_id}?i={source.id}"
        return f"https://music.apple.com/{country}/song/_/{source.id}"
    if source.platform == "deezer":
        return f"https://www.deezer.com/track/{source.id}"
    if source.platform == "tidal":
        return f"https://tidal.com/track/{source.id}"
    if source.platform == "youtubeMusic":
        return f"https://music.youtube.com/watch?v={source.id}"
    if source.platform == "amazonMusic":
        if source.album_id:
            return f"https://music.amazon.com/albums/{source.album_id}?trackAsin={source.id}"
        return f"https://music.amazon.com/albums/{source.id}"
    return ""


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
