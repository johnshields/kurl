"""DDG SERP scrape for Beatport track URLs."""

import re

from clients.resolvers._serp import clean_title, primary_artist, serp_search
from utils.logging import get_logger

logger = get_logger()

_BEATPORT_TRACK = re.compile(r"beatport\.com/track/([^/\"' ]+)/(\d+)")
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if len(w) >= 4}


async def search_track_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    query = f"site:beatport.com/track {clean_title(title)} {primary_artist(artist)}"
    m = await serp_search(query, _BEATPORT_TRACK, label=f"beatport:{title}")
    if not m:
        return None

    # DDG often returns unrelated Beatport tracks. Require at least one
    # >=4-char title token to appear in the URL slug before trusting the hit.
    slug = m.group(1)
    slug_tokens = _tokens(slug)
    title_tokens = _tokens(clean_title(title))
    if title_tokens and not (title_tokens & slug_tokens):
        logger.info("Beatport slug mismatch for %s: slug=%s", title, slug)
        return None
    return f"https://www.beatport.com/track/{slug}/{m.group(2)}"
