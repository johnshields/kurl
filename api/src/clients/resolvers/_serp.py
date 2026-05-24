"""Shared SERP scrape helpers: DDG HTML + Bing HTML, first hit wins."""

import re
from urllib.parse import quote

from app.constants import SCRAPER_TIMEOUT, SCRAPER_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_DDG_URL = "https://duckduckgo.com/html/?q={query}"
_BING_URL = "https://www.bing.com/search?q={query}"


def _client(name: str):
    return get_client(
        name,
        timeout=SCRAPER_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


def primary_artist(artist: str) -> str:
    return artist.split(",")[0].split("&")[0].strip() or artist


async def serp_search(query: str, pattern: re.Pattern, *, label: str) -> re.Match | None:
    """Run DDG first, fall back to Bing. Return first regex match or None."""
    encoded = quote(query)
    for engine, url, client_name in (
        ("DDG", _DDG_URL, "serp_ddg"),
        ("Bing", _BING_URL, "serp_bing"),
    ):
        try:
            resp = await _client(client_name).get(url.format(query=encoded))
            if resp.status_code != 200:
                logger.warning("%s SERP %s -> %s", engine, label, resp.status_code)
                continue
            m = pattern.search(resp.text)
            if m:
                logger.info("%s SERP hit for %s", engine, label)
                return m
        except Exception as e:
            logger.warning("%s SERP failed for %s: %s", engine, label, e)
    return None
