"""Bandcamp autocomplete_elastic API -- track URL by title + artist."""

from app.constants import BANDCAMP_SEARCH_URL
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()


def _get_client():
    return get_client(
        "bandcamp_search",
        timeout=5.0,
        headers={"Content-Type": "application/json"},
    )


async def search_track_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    body = {
        "search_text": f"{artist} {title}",
        "search_filter": "t",
        "fan_id": None,
        "full_page": False,
    }
    try:
        resp = await _get_client().post(BANDCAMP_SEARCH_URL, json=body)
        if resp.status_code != 200:
            logger.warning("Bandcamp search %s -> %s", title, resp.status_code)
            return None
        for r in (resp.json().get("auto") or {}).get("results") or []:
            url = r.get("item_url_path")
            if url and ".bandcamp.com/track/" in url:
                return url
        logger.info("Bandcamp no track for %s - %s", artist, title)
    except Exception as e:
        logger.warning("Bandcamp search failed for %s - %s: %s", artist, title, e)
    return None
