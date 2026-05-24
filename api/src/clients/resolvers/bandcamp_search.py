"""Bandcamp public autocomplete API -- track URL lookup by title + artist."""

from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_SEARCH_URL = "https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic"


def _get_client():
    return get_client(
        "bandcamp_search",
        timeout=5.0,
        headers={"Content-Type": "application/json"},
    )


async def search_track_url(title: str, artist: str) -> str | None:
    """First Bandcamp track URL matching title + artist via autocomplete API."""
    if not title or not artist:
        return None
    body = {
        "search_text": f"{artist} {title}",
        "search_filter": "t",  # tracks only
        "fan_id": None,
        "full_page": False,
    }
    try:
        resp = await _get_client().post(_SEARCH_URL, json=body)
        if resp.status_code != 200:
            logger.warning("Bandcamp search %s -> %s", title, resp.status_code)
            return None
        results = (resp.json().get("auto") or {}).get("results") or []
        for r in results:
            url = r.get("item_url_path")
            if url and ".bandcamp.com/track/" in url:
                return url
        logger.info("Bandcamp no track result for %s - %s", artist, title)
        return None
    except Exception as e:
        logger.warning("Bandcamp search failed for %s - %s: %s", artist, title, e)
        return None
