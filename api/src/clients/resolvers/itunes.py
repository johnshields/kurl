"""iTunes Search API: canonical metadata + Apple Music URL + artwork."""

import json

from app.constants import ITUNES_SEARCH_URL, SCRAPER_USER_AGENT
from clients import cache
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

# Per-worker memo so artwork + URL lookups within one request share a call.
_search_cache: dict[tuple[str, str], dict | None] = {}

# Persisted to KV too -- cuts request volume against Apple's shared-pool rate limit.
_CACHE_TTL = 60 * 60 * 24 * 7


def _get_client():
    return get_client("itunes", timeout=3.0, headers={"User-Agent": SCRAPER_USER_AGENT})


async def _search_one(title: str, artist: str | None, entity: str = "song") -> dict | None:
    key = (entity, title, artist or "")
    if key in _search_cache:
        return _search_cache[key]

    cache_key = f"itunes:{entity}:{title}:{artist or ''}"
    cached = await cache.get(cache_key)
    if cached is not None:
        result = json.loads(cached)
        _search_cache[key] = result
        return result

    query = f"{title} {artist}" if artist else title
    persist = True
    try:
        response = await _get_client().get(
            ITUNES_SEARCH_URL,
            params={"term": query, "entity": entity, "limit": 1, "media": "music"},
        )
        if response.status_code == 429:
            # Transient -- don't cache the miss.
            logger.warning("iTunes search rate-limited for %r", query)
            result = None
            persist = False
        elif response.status_code != 200:
            logger.warning("iTunes search returned %s for %r: %s", response.status_code, query, response.text[:200])
            result = None
        else:
            results = response.json().get("results") or []
            if not results:
                logger.info("iTunes search found no results for %r (entity=%s)", query, entity)
            result = results[0] if results else None
    except Exception as e:
        logger.warning("iTunes search failed: %s", e)
        result = None
        persist = False

    _search_cache[key] = result
    if persist:
        await cache.set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


async def fetch_artwork(title: str | None, artist: str | None) -> str | None:
    """Hi-res cover URL."""
    if not title:
        return None
    result = await _search_one(title, artist)
    if not result:
        return None
    art = result.get("artworkUrl100")
    return art.replace("100x100bb", "600x600bb") if art else None


async def fetch_apple_music_url(title: str | None, artist: str | None) -> str | None:
    """Canonical music.apple.com track URL."""
    if not title:
        return None
    result = await _search_one(title, artist)
    return result.get("trackViewUrl") if result else None


async def canonicalise(title: str | None, artist: str | None) -> tuple[str | None, str | None]:
    """Snap title + artist to iTunes' catalogue values; passthrough on miss."""
    if not title:
        return title, artist
    result = await _search_one(title, artist)
    if not result:
        return title, artist
    return result.get("trackName") or title, result.get("artistName") or artist


async def fetch_apple_album_url(title: str | None, artist: str | None) -> str | None:
    """Canonical music.apple.com album URL via iTunes Search."""
    if not title:
        return None
    result = await _search_one(title, artist, entity="album")
    return result.get("collectionViewUrl") if result else None
