import json
import re
from urllib.parse import urlparse

import httpx

from app.constants import SCRAPER_TIMEOUT, SCRAPER_USER_AGENT, SPOTIFY_EMBED_URL, YOUTUBE_OEMBED_URL
from utils.logging import get_logger
from utils.scraping import (
    extract_next_data,
    extract_og_description,
    extract_og_title,
    split_title_by_artist,
    strip_platform_suffix,
    strip_release_suffix,
)
from utils.url_parser import ParsedTrack

logger = get_logger()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=SCRAPER_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": SCRAPER_USER_AGENT},
        )
    return _client


async def fetch_metadata(parsed: ParsedTrack, url: str) -> tuple[str | None, str | None]:
    """Fetch (title, artist) for a track via platform-specific scraping."""
    try:
        if parsed.platform == "spotify":
            return await _fetch_spotify(parsed.track_id)
        if parsed.platform == "youtubeMusic":
            return await _fetch_youtube(parsed.track_id)
        if parsed.platform == "soundcloud":
            return await _fetch_soundcloud(url)
        # Default: og scrape -- works for Apple Music, Tidal, Deezer, Bandcamp
        # track pages and gives at least a search-quality title.
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


# SoundCloud track pages embed hydration JSON with publisher_metadata
# (artist, ISRC, UPC). og:title alone misses the artist on many tracks
# because it's only the song title.
_SC_ARTIST = re.compile(r'"publisher_metadata":\s*\{[^}]*?"artist":"([^"]+)"')
_SC_RELEASE_TITLE = re.compile(r'"publisher_metadata":\s*\{[^}]*?"release_title":"([^"]+)"')


async def _fetch_soundcloud(url: str) -> tuple[str | None, str | None]:
    """SoundCloud track page hydration JSON > og tags for artist + title."""
    response = await _get_client().get(url)
    if response.status_code != 200:
        logger.warning("SoundCloud page returned %s", response.status_code)
        return None, None

    html = response.text
    title = None
    artist = None

    m = _SC_RELEASE_TITLE.search(html)
    if m:
        title = m.group(1)
    if not title:
        og_title = extract_og_title(html)
        if og_title:
            title = og_title

    m = _SC_ARTIST.search(html)
    if m:
        artist = m.group(1)

    # Fallback: first URL segment is artist handle (e.g. /deadmau5/strobe).
    if not artist:
        parts = [p for p in urlparse(url).path.split("/") if p]
        if parts:
            artist = parts[0]

    return title, artist


async def _fetch_youtube(video_id: str) -> tuple[str | None, str | None]:
    """YouTube oEmbed returns title + channel name -- no API key required."""
    response = await _get_client().get(YOUTUBE_OEMBED_URL.format(id=video_id))
    if response.status_code != 200:
        logger.warning("YouTube oEmbed returned %s", response.status_code)
        return None, None

    data = response.json()
    raw_title = data.get("title")
    author = data.get("author_name")
    if not raw_title:
        return None, None

    title, artist = _parse_youtube_title(raw_title, author)
    return title, artist


def _parse_youtube_title(raw: str, author: str | None) -> tuple[str, str | None]:
    """Parse 'Artist - Title' or fall back to channel name as artist."""
    cleaned = _strip_youtube_noise(raw)

    # Music video titles use "Artist <sep> Title" with sep = hyphen, en dash or em dash.
    for sep in (" - ", " \u2013 ", " \u2014 "):
        if sep in cleaned:
            left, right = cleaned.split(sep, 1)
            return right.strip(), left.strip()

    # Fall back to channel name (often "ArtistVEVO" or "Artist - Topic").
    artist = None
    if author:
        artist = author.removesuffix("VEVO").removesuffix(" - Topic").strip() or None

    return cleaned, artist


_YOUTUBE_NOISE_PATTERNS = (
    re.compile(
        r"\s*[\(\[][^\)\]]*(?:official|music|video|audio|lyrics?|hd|4k|mv|visualizer)[^\)\]]*[\)\]]",
        re.I,
    ),
    re.compile(r"\s*[\(\[][^\)\]]*(?:feat\.?|ft\.?)[^\)\]]*[\)\]]", re.I),
)


def _strip_youtube_noise(title: str) -> str:
    """Remove common YouTube suffixes like '(Official Music Video)'."""
    result = title
    for p in _YOUTUBE_NOISE_PATTERNS:
        result = p.sub("", result)
    return result.strip()


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

    title = strip_release_suffix(strip_platform_suffix(title))
    if artist:
        artist = strip_platform_suffix(artist)

    return title, artist
