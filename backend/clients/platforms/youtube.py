from app.config import settings
from app.constants import YOUTUBE_API_BASE
from clients.platforms._http import get_client
from utils.canonical_url import build_track_url
from utils.logging import get_logger

logger = get_logger()


async def _api_get(path: str, params: dict | None = None) -> dict:
    response = await get_client("youtube").get(
        f"{YOUTUBE_API_BASE}{path}",
        params={"key": settings.YOUTUBE_API_KEY, **(params or {})},
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.YOUTUBE_API_KEY)


async def get_track(video_id: str) -> dict:
    """GET /videos?part=snippet&id={video_id} -- returns first item or raises."""
    data = await _api_get("/videos", params={"part": "snippet", "id": video_id})
    items = data.get("items", [])
    if not items:
        raise ValueError(f"YouTube video not found: {video_id}")
    return items[0]


async def get_album(playlist_id: str) -> dict:
    """GET /playlists?part=snippet&id={playlist_id}."""
    data = await _api_get("/playlists", params={"part": "snippet", "id": playlist_id})
    items = data.get("items", [])
    if not items:
        raise ValueError(f"YouTube playlist not found: {playlist_id}")
    return items[0]


async def get_artist(channel_id: str) -> dict:
    """GET /channels?part=snippet&id={channel_id}."""
    data = await _api_get("/channels", params={"part": "snippet", "id": channel_id})
    items = data.get("items", [])
    if not items:
        raise ValueError(f"YouTube channel not found: {channel_id}")
    return items[0]


async def search_by_isrc(isrc: str) -> dict | None:
    # YouTube Data API v3 does not expose ISRC lookup.
    return None


async def search_by_upc(upc: str) -> dict | None:
    return None


async def search_track(title: str, artist: str) -> dict | None:
    """Search for a music video by title + artist. Returns a normalised item or None."""
    data = await _api_get("/search", params={
        "part": "snippet",
        "type": "video",
        "videoCategoryId": "10",
        "q": f"{artist} {title}",
        "maxResults": 1,
    })
    items = data.get("items", [])
    if not items:
        return None
    item = items[0]
    video_id = (item.get("id") or {}).get("videoId")
    if not video_id:
        return None
    # Normalise to same shape as videos.list items so extract_* functions work uniformly.
    return {"id": video_id, "snippet": item.get("snippet", {})}


async def search_artist(name: str) -> dict | None:
    """Search for a channel by name. Returns a normalised item or None."""
    data = await _api_get("/search", params={
        "part": "snippet",
        "type": "channel",
        "q": name,
        "maxResults": 1,
    })
    items = data.get("items", [])
    if not items:
        return None
    item = items[0]
    channel_id = (item.get("id") or {}).get("channelId")
    if not channel_id:
        return None
    return {"id": channel_id, "snippet": item.get("snippet", {})}


def extract_isrc(track: dict) -> str | None:
    return None


def extract_upc(album: dict) -> str | None:
    return None


def extract_track_url(track: dict) -> str | None:
    vid = track.get("id")
    return build_track_url("youtubeMusic", str(vid)) if vid else None


def extract_album_url(album: dict) -> str | None:
    aid = album.get("id")
    if isinstance(aid, dict):
        aid = aid.get("playlistId")
    return f"https://music.youtube.com/playlist?list={aid}" if aid else None


def extract_artist_url(artist: dict) -> str | None:
    return None


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    snippet = track.get("snippet", {})
    raw_title = snippet.get("title")
    channel = snippet.get("channelTitle")
    if not raw_title:
        return None, None
    return _parse_title(raw_title, channel)


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    snippet = album.get("snippet", {})
    return snippet.get("title"), snippet.get("channelTitle")


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("snippet", {}).get("title")


def _parse_title(raw: str, channel: str | None) -> tuple[str, str | None]:
    """Parse 'Artist - Title' format, falling back to channel name as artist."""
    for sep in (" - ", " \u2013 ", " \u2014 "):
        if sep in raw:
            left, right = raw.split(sep, 1)
            return right.strip(), left.strip()
    artist = None
    if channel:
        artist = channel.removesuffix("VEVO").removesuffix(" - Topic").strip() or None
    return raw, artist
