"""
Short link resolver
Follow shareable shortened URLs (spotify.link, dzr.page.link) to their
canonical page so the parser has a real URL to work with.
"""

import re
from urllib.parse import urlparse

from app.constants import SCRAPER_USER_AGENT, SHORT_LINK_HOSTS
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_META_REFRESH = re.compile(
    r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^"\'>\s]+)',
    re.I,
)
_OG_URL = re.compile(
    r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)


def _get_client():
    return get_client(
        "short_links",
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


def is_short_link(url: str) -> bool:
    host = (urlparse(url).netloc or "").lower()
    return host in SHORT_LINK_HOSTS


async def resolve_short_link(url: str) -> str:
    """Follow a short URL to its canonical destination, or return it unchanged on failure."""
    try:
        response = await _get_client().get(url)
        final = str(response.url)

        # HTTP follow already landed on the canonical host.
        host = urlparse(final).netloc.lower()
        if host not in SHORT_LINK_HOSTS:
            logger.info("Short link %s -> %s (via redirect)", url, final)
            return final

        # spotify.link redirects via JS -- pull the canonical URL from the landing page.
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
