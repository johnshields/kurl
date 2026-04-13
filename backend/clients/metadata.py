import json
import re

import httpx

from utils.logging import get_logger

logger = get_logger()

_client: httpx.AsyncClient | None = None

_OG_TITLE = re.compile(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', re.I)
_OG_DESC = re.compile(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', re.I)
_NEXT_DATA = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>')
_BY_SPLIT = re.compile(r"^(.*?)\s+by\s+(.+)$", re.I)
_PLATFORM_SUFFIX = re.compile(r"\s+on\s+(Apple\s*Music|Spotify|YouTube\s*Music|Deezer|Tidal|Amazon\s*Music|Pandora)\s*$", re.I)
_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers={"User-Agent": _USER_AGENT})
    return _client


async def fetch_metadata(platform: str, url: str, track_id: str | None = None) -> tuple[str | None, str | None]:
    """Fetch (title, artist) for a track URL via platform-specific scraping."""
    try:
        if platform == "spotify" and track_id:
            return await _fetch_spotify(track_id)
        if platform == "appleMusic":
            return await _fetch_og(url)
    except Exception as e:
        logger.warning("Metadata fetch failed for %s: %s", platform, e)
    return None, None


async def _fetch_spotify(track_id: str) -> tuple[str | None, str | None]:
    """Spotify embed pages include full track data in __NEXT_DATA__."""
    response = await _get_client().get(f"https://open.spotify.com/embed/track/{track_id}")
    if response.status_code != 200:
        logger.warning("Spotify embed returned %s", response.status_code)
        return None, None

    match = _NEXT_DATA.search(response.text)
    if not match:
        return None, None

    data = json.loads(match.group(1))
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

    html = response.text
    og_title = _match(_OG_TITLE, html)
    og_desc = _match(_OG_DESC, html)

    if not og_title:
        return None, None

    title = og_title
    artist: str | None = None

    by_match = _BY_SPLIT.match(og_title)
    if by_match:
        title = by_match.group(1).strip()
        artist = by_match.group(2).strip()

    if not artist and og_desc:
        for sep in ("·", "•", "-"):
            if sep in og_desc:
                first = og_desc.split(sep)[0].strip()
                if first and first.lower() != title.lower():
                    artist = first
                    break

    if artist:
        artist = _PLATFORM_SUFFIX.sub("", artist).strip()
    if title:
        title = _PLATFORM_SUFFIX.sub("", title).strip()

    return title, artist


def _match(pattern: re.Pattern, html: str) -> str | None:
    m = pattern.search(html)
    return m.group(1).strip() if m else None
