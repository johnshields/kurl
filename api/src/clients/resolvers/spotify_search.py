"""DuckDuckGo SERP scrape for Spotify track URLs."""

import re
from urllib.parse import quote

from app.constants import SCRAPER_TIMEOUT, SCRAPER_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_DDG_URL = "https://duckduckgo.com/html/?q={query}"
_SPOTIFY_TRACK = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]{22})")


def _get_client():
    return get_client(
        "spotify_search",
        timeout=SCRAPER_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


async def search_track_url(title: str, artist: str) -> str | None:
    """First Spotify track URL from a DuckDuckGo site-restricted search."""
    if not title or not artist:
        return None
    query = f'site:open.spotify.com/track "{title}" "{artist}"'
    try:
        resp = await _get_client().get(_DDG_URL.format(query=quote(query)))
        if resp.status_code != 200:
            logger.warning("DDG SERP %s -> %s", title, resp.status_code)
            return None
        m = _SPOTIFY_TRACK.search(resp.text)
        if not m:
            logger.info("DDG no Spotify result for %s - %s", artist, title)
            return None
        return f"https://open.spotify.com/track/{m.group(1)}"
    except Exception as e:
        logger.warning("DDG scrape failed for %s - %s: %s", artist, title, e)
        return None
