"""DDG SERP scrape for Beatport track and release URLs."""

import re

from clients.resolvers._serp import clean_title, primary_artist, serp_search
from utils.logging import get_logger

logger = get_logger()

_BEATPORT_TRACK = re.compile(r"beatport\.com/track/([^/\"' ]+)/(\d+)")
_BEATPORT_RELEASE = re.compile(r"beatport\.com/release/([^/\"' ]+)/(\d+)")
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if len(w) >= 4}


def _verify(slug: str, title: str, kind: str) -> bool:
    slug_tokens = _tokens(slug)
    title_tokens = _tokens(clean_title(title))
    if title_tokens and not (title_tokens & slug_tokens):
        logger.info("Beatport %s slug mismatch for %s: slug=%s", kind, title, slug)
        return False
    return True


async def search_track_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    query = f"site:beatport.com/track {clean_title(title)} {primary_artist(artist)}"
    m = await serp_search(query, _BEATPORT_TRACK, label=f"beatport:{title}")
    if not m or not _verify(m.group(1), title, "track"):
        return None
    return f"https://www.beatport.com/track/{m.group(1)}/{m.group(2)}"


async def search_album_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    query = f"site:beatport.com/release {clean_title(title)} {primary_artist(artist)}"
    m = await serp_search(query, _BEATPORT_RELEASE, label=f"beatport-album:{title}")
    if not m or not _verify(m.group(1), title, "release"):
        return None
    return f"https://www.beatport.com/release/{m.group(1)}/{m.group(2)}"
