"""DDG SERP scrape helper."""

import re
from urllib.parse import quote

from app.constants import DDG_SEARCH_URL, SCRAPER_TIMEOUT, SCRAPER_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()


def _client():
    return get_client(
        "serp",
        timeout=SCRAPER_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


def primary_artist(artist: str) -> str:
    primary = artist.split(",")[0].split("&")[0].strip().rstrip(".")
    return primary or artist


_BRACKETED = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*")


def clean_title(title: str) -> str:
    """Strip bracketed suffixes like (feat. X), (Original Mix), [Remix]."""
    cleaned = _BRACKETED.sub(" ", title).strip()
    return cleaned or title


async def serp_search(query: str, pattern: re.Pattern, *, label: str) -> re.Match | None:
    """First regex match from DDG HTML SERP, or None."""
    logger.info("DDG SERP %s: %s", label, query)
    try:
        resp = await _client().get(DDG_SEARCH_URL.format(query=quote(query)))
        if resp.status_code != 200:
            logger.warning("DDG SERP %s -> %s", label, resp.status_code)
            return None
        m = pattern.search(resp.text)
        if not m:
            logger.info("DDG SERP no match for %s", label)
            return None
        return m
    except Exception as e:
        logger.warning("DDG SERP failed for %s: %s", label, e)
        return None
