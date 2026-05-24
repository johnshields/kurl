"""SERP scrape (DDG + Bing) for Beatport track URLs."""

import re

from clients.resolvers._serp import primary_artist, serp_search

_BEATPORT_TRACK = re.compile(r"beatport\.com/track/([^/\"' ]+)/(\d+)")


async def search_track_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    query = f"site:beatport.com/track {title} {primary_artist(artist)}"
    m = await serp_search(query, _BEATPORT_TRACK, label=f"beatport:{title}")
    return f"https://www.beatport.com/track/{m.group(1)}/{m.group(2)}" if m else None
