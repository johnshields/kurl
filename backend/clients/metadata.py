import json

import httpx

from app.constants import SCRAPER_USER_AGENT, SPOTIFY_EMBED_URL
from utils.logging import get_logger
from utils.scraping import (
    extract_next_data,
    extract_og_description,
    extract_og_title,
    split_title_by_artist,
    strip_platform_suffix,
)
from utils.url_parser import ParsedTrack

logger = get_logger()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
            headers={"User-Agent": SCRAPER_USER_AGENT},
        )
    return _client


async def fetch_metadata(parsed: ParsedTrack, url: str) -> tuple[str | None, str | None]:
    """Fetch (title, artist) for a track via platform-specific scraping."""
    try:
        if parsed.platform == "spotify":
            return await _fetch_spotify(parsed.track_id)
        if parsed.platform == "appleMusic":
            return await _fetch_og(url)
    except Exception as e:
        logger.warning("Metadata fetch failed for %s: %s", parsed.platform, e)
    return None, None


async def _fetch_spotify(track_id: str) -> tuple[str | None, str | None]:
    """Spotify embed pages include full track data in __NEXT_DATA__."""
    response = await _get_client().get(SPOTIFY_EMBED_URL.format(id=track_id))
    if response.status_code != 200:
        logger.warning("Spotify embed returned %s", response.status_code)
        return None, None

    raw = extract_next_data(response.text)
    if not raw:
        return None, None

    data = json.loads(raw)
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
    title = entity.get("title")
    artists = [a.get("name") for a in entity.get("artists", []) if a.get("name")]
    return title, ", ".join(artists) if artists else None


async def _fetch_og(url: str) -> tuple[str | None, str | None]:
    """Scrape og:title and og:description from a track page."""
    response = await _get_client().get(url)
    if response.status_code != 200:
        logger.warning("og fetch returned %s", response.status_code)
        return None, None

    og_title = extract_og_title(response.text)
    og_desc = extract_og_description(response.text)
    if not og_title:
        return None, None

    title, artist = split_title_by_artist(og_title)

    if not artist and og_desc:
        for sep in ("·", "•", "-"):
            if sep in og_desc:
                first = og_desc.split(sep)[0].strip()
                if first and first.lower() != title.lower():
                    artist = first
                    break

    title = strip_platform_suffix(title)
    if artist:
        artist = strip_platform_suffix(artist)

    return title, artist
