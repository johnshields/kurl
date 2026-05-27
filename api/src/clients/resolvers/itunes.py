"""iTunes Search API: canonical metadata + Apple Music URL + artwork."""

from app.constants import ITUNES_SEARCH_URL, SCRAPER_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

# Per-worker memo so artwork + URL lookups share one request.
_search_cache: dict[tuple[str, str], dict | None] = {}


def _get_client():
    return get_client("itunes", timeout=3.0, headers={"User-Agent": SCRAPER_USER_AGENT})


async def _search_one(title: str, artist: str | None, entity: str = "song") -> dict | None:
    key = (entity, title, artist or "")
    if key in _search_cache:
        return _search_cache[key]
    query = f"{title} {artist}" if artist else title
    try:
        response = await _get_client().get(
            ITUNES_SEARCH_URL,
            params={"term": query, "entity": entity, "limit": 1, "media": "music"},
        )
        if response.status_code != 200:
            _search_cache[key] = None
            return None
        results = response.json().get("results") or []
        result = results[0] if results else None
    except Exception as e:
        logger.warning("iTunes search failed: %s", e)
        result = None
    _search_cache[key] = result
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
