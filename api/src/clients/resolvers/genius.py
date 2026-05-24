"""Genius API resolver: title + artist -> streaming URLs via song media[]."""

from app.config import settings
from app.constants import GENIUS_API_BASE
from clients._http import get_client
from clients.resolvers._serp import clean_title, primary_artist
from utils.logging import get_logger

logger = get_logger()

# Genius media provider -> our platform id.
_PROVIDER_MAP = {
    "spotify": "spotify",
    "apple_music": "appleMusic",
    "youtube": "youtubeMusic",
}


def _get_client():
    return get_client(
        "genius",
        timeout=5.0,
        headers={"Authorization": f"Bearer {settings.GENIUS_ACCESS_TOKEN}"},
    )


def is_configured() -> bool:
    return bool(settings.GENIUS_ACCESS_TOKEN)


async def _search_song_id(title: str, artist: str) -> int | None:
    query = f"{primary_artist(artist)} {clean_title(title)}"
    try:
        resp = await _get_client().get(f"{GENIUS_API_BASE}/search", params={"q": query})
        if resp.status_code != 200:
            logger.warning("Genius search %s -> %s", title, resp.status_code)
            return None
        hits = (resp.json().get("response") or {}).get("hits") or []
        if not hits:
            logger.info("Genius no hits for %s - %s", artist, title)
            return None
        return (hits[0].get("result") or {}).get("id")
    except Exception as e:
        logger.warning("Genius search failed for %s - %s: %s", artist, title, e)
        return None


async def search_url(title: str, artist: str, platform: str) -> str | None:
    """Resolve title + artist to a streaming URL on the target platform."""
    if not title or not artist or not is_configured():
        return None

    song_id = await _search_song_id(title, artist)
    if not song_id:
        return None

    try:
        resp = await _get_client().get(f"{GENIUS_API_BASE}/songs/{song_id}")
        if resp.status_code != 200:
            logger.warning("Genius song %s -> %s", song_id, resp.status_code)
            return None
        media = ((resp.json().get("response") or {}).get("song") or {}).get("media") or []
        for entry in media:
            if _PROVIDER_MAP.get(entry.get("provider")) == platform:
                return entry.get("url")
        logger.info("Genius song %s has no %s media", song_id, platform)
    except Exception as e:
        logger.warning("Genius song fetch failed for %s: %s", song_id, e)
    return None


async def spotify_url(title: str, artist: str) -> str | None:
    return await search_url(title, artist, "spotify")


async def apple_url(title: str, artist: str) -> str | None:
    return await search_url(title, artist, "appleMusic")


async def youtube_url(title: str, artist: str) -> str | None:
    return await search_url(title, artist, "youtubeMusic")
