import re

from app.config import settings
from app.constants import SOUNDCLOUD_API_BASE, SOUNDCLOUD_TOKEN_URL
from clients.platforms._http import get_client
from clients.platforms._oauth import TokenCache
from utils.canonical_url import build_track_url
from utils.logging import get_logger

logger = get_logger()

_tokens = TokenCache("SoundCloud")


async def _get_token() -> str:
    return await _tokens.fetch_via_oauth(
        get_client("soundcloud", follow_redirects=True),
        SOUNDCLOUD_TOKEN_URL,
        settings.SOUNDCLOUD_CLIENT_ID,
        settings.SOUNDCLOUD_CLIENT_SECRET,
    )


async def _api_get(path: str, params: dict | None = None) -> dict | list:
    token = await _get_token()
    response = await get_client("soundcloud", follow_redirects=True).get(
        f"{SOUNDCLOUD_API_BASE}{path}",
        headers={"Authorization": f"OAuth {token}"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.SOUNDCLOUD_CLIENT_ID and settings.SOUNDCLOUD_CLIENT_SECRET)


async def _resolve(url: str) -> dict:
    """Resolve any SoundCloud permalink URL to its resource object."""
    return await _api_get("/resolve", params={"url": url})


async def get_track(track_id: str) -> dict:
    """Fetch a track by permalink path (user/slug) or numeric ID."""
    if "/" in track_id:
        return await _resolve(f"https://soundcloud.com/{track_id}")
    return await _api_get(f"/tracks/{track_id}")


async def get_album(playlist_id: str) -> dict:
    """Fetch a playlist/set by permalink path or numeric ID."""
    if "/" in playlist_id:
        return await _resolve(f"https://soundcloud.com/{playlist_id}")
    return await _api_get(f"/playlists/{playlist_id}")


async def get_artist(user_id: str) -> dict:
    """Fetch a user profile by permalink slug or numeric ID."""
    if not user_id.isdigit():
        return await _resolve(f"https://soundcloud.com/{user_id}")
    return await _api_get(f"/users/{user_id}")


async def search_by_isrc(isrc: str) -> dict | None:
    """Filter tracks by ISRC. SoundCloud's /tracks endpoint silently ignores
    unknown query params, so verify the returned track's publisher_metadata.isrc
    matches to avoid returning a random track.
    """
    data = await _api_get("/tracks", params={"isrc": isrc, "limit": 1})
    items = data if isinstance(data, list) else data.get("collection", [])
    if not items:
        return None
    track = items[0]
    if (track.get("publisher_metadata") or {}).get("isrc") != isrc:
        return None
    return track


async def search_by_upc(upc: str) -> dict | None:
    return None


async def search_track(title: str, artist: str) -> dict | None:
    """Free-text track search. Only returns a result if the uploading account
    matches the target artist — otherwise falls through to the search URL.
    SoundCloud is mostly user uploads, so without an artist-account match we
    can't trust the result to be the original.
    """
    data = await _api_get("/tracks", params={"q": f"{artist} {title}", "limit": 10})
    items = data if isinstance(data, list) else data.get("collection", [])
    for track in items:
        if _artist_matches(track, artist):
            return track
    return None


def _artist_matches(track: dict, target_artist: str) -> bool:
    target = _slug(target_artist)
    if not target:
        return False
    user = track.get("user") or {}
    pub = track.get("publisher_metadata") or {}
    candidates = (user.get("username"), user.get("permalink"), pub.get("artist"))
    return any(target in _slug(c) for c in candidates if c)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


async def search_artist(name: str) -> dict | None:
    """Free-text user search. Returns the first match or None."""
    data = await _api_get("/users", params={"q": name, "limit": 1})
    items = data if isinstance(data, list) else data.get("collection", [])
    return items[0] if items else None


def extract_isrc(track: dict) -> str | None:
    return (track.get("publisher_metadata") or {}).get("isrc")


def extract_upc(album: dict) -> str | None:
    return None


def extract_track_url(track: dict) -> str | None:
    url = track.get("permalink_url")
    if url:
        return url
    user = (track.get("user") or {}).get("permalink")
    slug = track.get("permalink")
    if user and slug:
        return build_track_url("soundcloud", f"{user}/{slug}")
    return None


def extract_album_url(album: dict) -> str | None:
    return album.get("permalink_url")


def extract_artist_url(artist: dict) -> str | None:
    return artist.get("permalink_url")


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    title = track.get("title")
    pub = track.get("publisher_metadata") or {}
    user = track.get("user") or {}
    artist = pub.get("artist") or user.get("username")
    return title, artist


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    title = album.get("title")
    user = album.get("user") or {}
    return title, user.get("username")


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("username")
