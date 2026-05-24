"""ISRC -> platform URL via MusicBrainz recording URL relations."""

import re

from app.constants import MUSICBRAINZ_APIMUSICBRAINZ_API_BASE, MUSICBRAINZMUSICBRAINZ_USER_AGENT
from clients._http import get_client
from utils.logging import get_logger

logger = get_logger()

_PLATFORM_PATTERNS = {
    "spotify": re.compile(r"https?://open\.spotify\.com/track/[A-Za-z0-9]+"),
    "appleMusic": re.compile(r"https?://music\.apple\.com/[^\s\"']+"),
    "youtubeMusic": re.compile(r"https?://music\.youtube\.com/watch\?v=[A-Za-z0-9_-]+"),
}


def _get_client():
    return get_client(
        "musicbrainz",
        headers={"User-Agent": MUSICBRAINZ_USER_AGENT, "Accept": "application/json"},
    )


async def lookup_url(isrc: str, platform: str) -> str | None:
    """Resolve ISRC to canonical URL on target platform."""
    pattern = _PLATFORM_PATTERNS.get(platform)
    if not pattern:
        return None
    try:
        resp = await _get_client().get(
            f"{MUSICBRAINZ_API_BASE}/recording",
            params={"query": f"isrc:{isrc}", "fmt": "json", "limit": 1},
        )
        if resp.status_code != 200:
            return None
        recordings = resp.json().get("recordings") or []
        if not recordings:
            return None
        mbid = recordings[0].get("id")
        if not mbid:
            return None

        resp = await _get_client().get(
            f"{MUSICBRAINZ_API_BASE}/recording/{mbid}",
            params={"inc": "url-rels", "fmt": "json"},
        )
        if resp.status_code != 200:
            return None
        for rel in resp.json().get("relations") or []:
            url = (rel.get("url") or {}).get("resource", "")
            m = pattern.search(url)
            if m:
                return m.group(0)
    except Exception as e:
        logger.warning("MusicBrainz lookup failed for %s/%s: %s", platform, isrc, e)
    return None
