import json
from dataclasses import dataclass

from app.constants import DEFAULT_STOREFRONT, RESCUE_PLATFORMS
from clients import cache, metadata
from clients.resolvers import bandcamp_search, beatport_search, genius, itunes, lastfm, spotify_search
from clients.platforms import apple, deezer, soundcloud, spotify, tidal, youtube
from utils.url.canonical_url import build_track_url
from utils.logging import get_logger
from utils.url.url_parser import ParsedMusicUrl, ParsedTrack

logger = get_logger()

_CLIENTS = {
    "spotify": spotify,
    "appleMusic": apple,
    "deezer": deezer,
    "tidal": tidal,
    "youtubeMusic": youtube,
    "soundcloud": soundcloud,
}


# Exact-match via labels; anything outside this set is a fallback.
EXACT_VIAS = frozenset({"isrc", "upc", "name", "search_api", "direct"})


def is_exact(via: str) -> bool:
    return via in EXACT_VIAS


@dataclass
class KurlMatch:
    url: str
    title: str | None = None
    artist: str | None = None
    via: str = "isrc"


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
    """Resolve source URL to target via ISRC/UPC/name. None = fall back to Odesli."""
    # Rescue targets resolve via third-party resolvers; native client optional.
    if not _get_client(target_platform) and target_platform not in RESCUE_PLATFORMS:
        return None

    if source.entity_type == "track":
        return await _kurl_track(source, target_platform)

    if source.entity_type == "album":
        return await _kurl_album(source, target_platform)

    if source.entity_type == "artist":
        return await _kurl_artist(source, target_platform)

    return None


async def _kurl_track(source: ParsedMusicUrl, target_platform: str) -> KurlMatch | None:
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

    if not title or not artist:
        scraped_title, scraped_artist, _ = await metadata.fetch_metadata(
            ParsedTrack(source.platform, source.id),
            _build_source_url(source),
        )
        title = title or scraped_title
        artist = artist or scraped_artist

    if not title or not artist:
        return None

    if target_platform in RESCUE_PLATFORMS:
        rescued = await _rescue_url(target_platform, title, artist)
        if rescued:
            return KurlMatch(url=rescued, title=title, artist=artist, via="isrc")

    return await _search_track_by_metadata(target_platform, title, artist)


# (module, attr, label) per target; attr lookup at call time keeps test patches working.
_RESCUE_CHAIN = {
    "appleMusic": [
        (itunes, "fetch_apple_music_url", "iTunes Search"),
        (genius, "apple_url", "Genius"),
    ],
    "spotify": [
        (lastfm, "spotify_url", "Last.fm"),
        (spotify_search, "search_track_url", "DDG search"),
        (genius, "spotify_url", "Genius"),
    ],
    "youtubeMusic": [(genius, "youtube_url", "Genius")],
    "beatport": [(beatport_search, "search_track_url", "DDG search")],
    "bandcamp": [(bandcamp_search, "search_track_url", "search API")],
}


async def _rescue_url(target_platform: str, title: str, artist: str) -> str | None:
    """Last-ditch URL resolution; tries each resolver in order until one hits."""
    for mod, attr, label in _RESCUE_CHAIN.get(target_platform, []):
        url = await getattr(mod, attr)(title, artist)
        if url:
            logger.info("Rescued %s URL via %s: %s", target_platform, label, url)
            return url
    return None


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
    """Artist match by name. Lower confidence than ISRC/UPC."""
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
    """Fetch (identifier, title, artist) from source. Cached by entity."""
    cache_key = f"{label.lower()}:{source.platform}:{source.entity_type}:{source.id}"
    cached = await cache.get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            logger.info("Cache hit %s: %s", cache_key, data.get("id"))
            return data.get("id"), data.get("title"), data.get("artist")
        except Exception:
            pass

    client = _get_client(source.platform)
    identifier: str | None = None
    title: str | None = None
    artist: str | None = None

    if client:
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
        except Exception as e:
            logger.warning("Failed to get %s from %s API: %s", label, source.platform, e)

    # Scrape source page; backfill ISRC via Deezer search if still missing.
    if not identifier and label == "ISRC" and source.entity_type == "track":
        scraped_title, scraped_artist, scraped_isrc = await metadata.fetch_metadata(
            ParsedTrack(source.platform, source.id),
            _build_source_url(source),
        )
        title = title or scraped_title
        artist = artist or scraped_artist

        if scraped_isrc:
            identifier = scraped_isrc
            logger.info("Source %s ISRC=%s (via scrape)", source.platform, identifier)
        elif title and artist:
            try:
                dz = await deezer.search_track(title, artist)
                if dz:
                    identifier = deezer.extract_isrc(dz)
                    if identifier:
                        logger.info(
                            "Source %s ISRC=%s (via Deezer oracle)",
                            source.platform,
                            identifier,
                        )
            except Exception as e:
                logger.warning("Deezer ISRC oracle failed: %s", e)

    if identifier:
        await cache.set(
            cache_key,
            json.dumps({"id": identifier, "title": title, "artist": artist}),
        )

    return identifier, title, artist


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
    """Search target by identifier; build KurlMatch."""
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
    """Search target by title + artist. Lower confidence than ISRC."""
    client = _get_client(target_platform)
    if not client or not hasattr(client, "search_track"):
        return None

    # Trim CSV credits to primary; full classical/feat strings tank match quality.
    primary_artist = artist.split(",")[0].strip() or artist

    try:
        match = await client.search_track(title, primary_artist, **_ctx(target_platform))
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
    return build_track_url(source.platform, source.id, source.country, source.album_id)
