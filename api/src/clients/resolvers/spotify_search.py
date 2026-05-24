"""DDG SERP scrape for Spotify track URLs."""

import re

from clients.resolvers._serp import primary_artist, serp_search

_SPOTIFY_TRACK = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]{22})")


async def search_track_url(title: str, artist: str) -> str | None:
    if not title or not artist:
        return None
    query = f"site:open.spotify.com/track {title} {primary_artist(artist)}"
    m = await serp_search(query, _SPOTIFY_TRACK, label=f"spotify:{title}")
    return f"https://open.spotify.com/track/{m.group(1)}" if m else None
