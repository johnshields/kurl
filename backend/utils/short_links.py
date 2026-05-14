"""
Short link resolver
Spotify and Deezer issue shareable shortened URLs (spotify.link, dzr.page.link)
that redirect to the canonical track page. Follow the redirect server-side so
the parser has something to work with.

Spotify's spotify.link currently uses a JS-side redirect; the HTML response
embeds an og:url or refresh meta tag pointing to the canonical open.spotify.com
URL. Deezer's dzr.page.link is a plain HTTP 302.
"""

import re
from urllib.parse import urlparse

import httpx

from app.constants import CLIENT_TIMEOUT, SCRAPER_USER_AGENT
from utils.logging import get_logger

logger = get_logger()

_client: httpx.AsyncClient | None = None

SHORT_LINK_HOSTS = {"spotify.link", "dzr.page.link", "on.soundcloud.com"}

_META_REFRESH = re.compile(
    r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^"\'>\s]+)',
    re.I,
)
_OG_URL = re.compile(
    r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=CLIENT_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": SCRAPER_USER_AGENT},
        )
    return _client


def is_short_link(url: str) -> bool:
    host = (urlparse(url).netloc or "").lower()
    return host in SHORT_LINK_HOSTS


async def resolve_short_link(url: str) -> str:
    """Follow a short URL to its canonical destination.

    Returns the resolved URL, or the original URL if resolution fails.
    """
    try:
        response = await _get_client().get(url)
        final = str(response.url)

        # If the HTTP follow landed on the canonical host already, done.
        host = urlparse(final).netloc.lower()
        if host not in SHORT_LINK_HOSTS:
            logger.info("Short link %s -> %s (via redirect)", url, final)
            return final

        # Spotify: look for og:url or meta refresh inside the landing page.
        og_match = _OG_URL.search(response.text)
        if og_match:
            resolved = og_match.group(1)
            logger.info("Short link %s -> %s (via og:url)", url, resolved)
            return resolved

        refresh_match = _META_REFRESH.search(response.text)
        if refresh_match:
            resolved = refresh_match.group(1)
            logger.info("Short link %s -> %s (via meta refresh)", url, resolved)
            return resolved

        logger.warning("Could not resolve short link: %s", url)
        return url
    except Exception as e:
        logger.warning("Short link resolution failed for %s: %s", url, e)
        return url
