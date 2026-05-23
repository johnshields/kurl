"""
iTunes Search API artwork fetch.
Free, no auth. https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/
"""

import httpx

from app.constants import SCRAPER_USER_AGENT
from utils.logging import get_logger

logger = get_logger()

_SEARCH_URL = "https://itunes.apple.com/search"
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=3.0,
            headers={"User-Agent": SCRAPER_USER_AGENT},
        )
    return _client


async def fetch_artwork(title: str | None, artist: str | None) -> str | None:
    """Search iTunes for a song, return hi-res artwork URL or None."""
    if not title:
        return None
    query = f"{title} {artist}" if artist else title
    try:
        response = await _get_client().get(
            _SEARCH_URL,
            params={"term": query, "entity": "song", "limit": 1, "media": "music"},
        )
        if response.status_code != 200:
            return None
        results = response.json().get("results") or []
        if not results:
            return None
        # artworkUrl100 = "...100x100bb.jpg" -- swap to 600 for hi-res.
        art = results[0].get("artworkUrl100")
        if not art:
            return None
        return art.replace("100x100bb", "600x600bb")
    except Exception as e:
        logger.warning("iTunes artwork fetch failed: %s", e)
        return None
