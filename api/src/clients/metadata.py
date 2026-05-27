import html
import json
import re
from urllib.parse import urlparse

from app.constants import SCRAPER_TIMEOUT, SCRAPER_USER_AGENT, SPOTIFY_EMBED_URL, YOUTUBE_OEMBED_URL
from clients._http import get_client
from utils.logging import get_logger
from utils.scraping import (
    extract_next_data,
    extract_og_description,
    extract_og_title,
    split_title_by_artist,
    strip_platform_suffix,
    strip_release_suffix,
)
from utils.url.url_parser import ParsedTrack

logger = get_logger()

# ISRC: CC + 3-char registrant + YY + 5-digit designation, anywhere in page JSON.
_ISRC_PATTERN = re.compile(r'"isrc"\s*:\s*"([A-Z]{2}[A-Z0-9]{3}\d{7})"', re.I)


def _clean(s: str | None) -> str | None:
    """Decode HTML entities (&#39; -> ') and trim whitespace."""
    return html.unescape(s).strip() if s else s


def _get_client():
    return get_client(
        "metadata",
        timeout=SCRAPER_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    )


def _isrc(html: str) -> str | None:
    m = _ISRC_PATTERN.search(html)
    return m.group(1).upper() if m else None


async def fetch_metadata(parsed: ParsedTrack, url: str) -> tuple[str | None, str | None, str | None]:
    """Scrape (title, artist, isrc) from a track page. ISRC only when embedded."""
    try:
        if parsed.platform == "spotify":
            return await _fetch_spotify(parsed.track_id)
        if parsed.platform == "youtubeMusic":
            return await _fetch_youtube(parsed.track_id)
        if parsed.platform == "soundcloud":
            return await _fetch_soundcloud(url)
        return await _fetch_og(url)
    except Exception as e:
        logger.warning("Metadata fetch failed for %s: %s", parsed.platform, e)
    return None, None, None


async def _fetch_spotify(track_id: str) -> tuple[str | None, str | None, str | None]:
    """Spotify embed page; data in __NEXT_DATA__."""
    response = await _get_client().get(SPOTIFY_EMBED_URL.format(id=track_id))
    if response.status_code != 200:
        logger.warning("Spotify embed returned %s", response.status_code)
        return None, None, None

    raw = extract_next_data(response.text)
    if not raw:
        return None, None, _isrc(response.text)

    data = json.loads(raw)
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
    title = entity.get("title")
    artists = [a.get("name") for a in entity.get("artists", []) if a.get("name")]
    artist = ", ".join(artists) if artists else None
    return _clean(title), _clean(artist), _isrc(response.text)


# SoundCloud hydration JSON; og:title alone misses artist on many tracks.
_SC_ARTIST = re.compile(r'"publisher_metadata":\s*\{[^}]*?"artist":"([^"]+)"')
_SC_RELEASE_TITLE = re.compile(r'"publisher_metadata":\s*\{[^}]*?"release_title":"([^"]+)"')


async def _fetch_soundcloud(url: str) -> tuple[str | None, str | None, str | None]:
    """SoundCloud publisher_metadata: artist + release_title + ISRC."""
    response = await _get_client().get(url)
    if response.status_code != 200:
        logger.warning("SoundCloud page returned %s", response.status_code)
        return None, None, None

    html = response.text
    m = _SC_RELEASE_TITLE.search(html)
    title = m.group(1) if m else extract_og_title(html)

    m = _SC_ARTIST.search(html)
    artist = m.group(1) if m else None

    # Fallback: first URL segment is the artist handle.
    if not artist:
        parts = [p for p in urlparse(url).path.split("/") if p]
        if parts:
            artist = parts[0]

    return _clean(title), _clean(artist), _isrc(html)


async def _fetch_youtube(video_id: str) -> tuple[str | None, str | None, str | None]:
    """YouTube oEmbed: title + channel. No ISRC."""
    response = await _get_client().get(YOUTUBE_OEMBED_URL.format(id=video_id))
    if response.status_code != 200:
        logger.warning("YouTube oEmbed returned %s", response.status_code)
        return None, None, None

    data = response.json()
    raw_title = data.get("title")
    author = data.get("author_name")
    if not raw_title:
        return None, None, None

    title, artist = _parse_youtube_title(_clean(raw_title) or "", _clean(author))
    return title, artist, None


def _parse_youtube_title(raw: str, author: str | None) -> tuple[str, str | None]:
    """Split 'Artist - Title'; fall back to channel name."""
    cleaned = _strip_youtube_noise(raw)

    for sep in (" - ", " – ", " — "):
        if sep in cleaned:
            left, right = cleaned.split(sep, 1)
            return right.strip(), left.strip()

    # Channels are often "ArtistVEVO" or "Artist - Topic".
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
    """Strip suffixes like '(Official Music Video)'."""
    result = title
    for p in _YOUTUBE_NOISE_PATTERNS:
        result = p.sub("", result)
    return result.strip()


async def _fetch_og(url: str) -> tuple[str | None, str | None, str | None]:
    """Generic og:title + og:description scrape."""
    response = await _get_client().get(url)
    if response.status_code != 200:
        logger.warning("og fetch returned %s", response.status_code)
        return None, None, None

    og_title = extract_og_title(response.text)
    og_desc = extract_og_description(response.text)
    if not og_title:
        return None, None, _isrc(response.text)

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

    return _clean(title), _clean(artist), _isrc(response.text)
