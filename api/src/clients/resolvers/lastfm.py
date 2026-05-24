"""Last.fm track-page scrape for embedded spotify:track URIs."""

import re
from urllib.parse import quote

from app.constants import LASTFM_TRACK_URL, SCRAPER_TIMEOUT, SCRAPER_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_SPOTIFY_URI = re.compile(r"spotify:track:([A-Za-z0-9]{22})")


def _get_client():
    return get_client(
        "lastfm",
        timeout=SCRAPER_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


async def spotify_url(title: str, artist: str) -> str | None:
    """Resolve title + artist to Spotify track URL via Last.fm page scrape."""
    if not title or not artist:
        return None
    try:
        url = LASTFM_TRACK_URL.format(artist=quote(artist), title=quote(title))
        resp = await _get_client().get(url)
        if resp.status_code != 200:
            return None
        m = _SPOTIFY_URI.search(resp.text)
        if not m:
            return None
        return f"https://open.spotify.com/track/{m.group(1)}"
    except Exception as e:
        logger.warning("Last.fm Spotify scrape failed for %s - %s: %s", artist, title, e)
        return None
