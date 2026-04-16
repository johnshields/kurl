import base64
import time

import httpx

from app.config import settings
from app.constants import CLIENT_TIMEOUT, DEFAULT_COUNTRY, TIDAL_ACCEPT_HEADER, TIDAL_API_BASE, TIDAL_TOKEN_URL
from utils.logging import get_logger

logger = get_logger()

_client: httpx.AsyncClient | None = None
_token: str | None = None
_token_expires_at: float = 0


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=CLIENT_TIMEOUT)
    return _client


async def _get_token() -> str:
    """Get a valid access token, refreshing if expired."""
    global _token, _token_expires_at

    if _token and time.time() < _token_expires_at - 60:
        return _token

    credentials = base64.b64encode(
        f"{settings.TIDAL_CLIENT_ID}:{settings.TIDAL_CLIENT_SECRET}".encode()
    ).decode()

    response = await _get_client().post(
        TIDAL_TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()

    data = response.json()
    _token = data["access_token"]
    _token_expires_at = time.time() + data.get("expires_in", 86400)
    logger.info("Tidal token refreshed, expires in %ss", data.get("expires_in"))
    return _token


async def _api_get(path: str, params: dict | None = None) -> dict:
    token = await _get_token()
    params = {**(params or {}), "countryCode": (params or {}).get("countryCode", DEFAULT_COUNTRY)}
    response = await _get_client().get(
        f"{TIDAL_API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": TIDAL_ACCEPT_HEADER,
        },
        params=params,
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.TIDAL_CLIENT_ID and settings.TIDAL_CLIENT_SECRET)


async def get_track(track_id: str) -> dict:
    """GET /tracks/{id} -- returns track object including isrc."""
    data = await _api_get(f"/tracks/{track_id}")
    return data.get("resource", data)


async def get_album(album_id: str) -> dict:
    """GET /albums/{id} -- returns album object including barcodeId (UPC)."""
    data = await _api_get(f"/albums/{album_id}")
    return data.get("resource", data)


async def get_artist(artist_id: str) -> dict:
    """GET /artists/{id} -- returns artist name, picture, etc."""
    data = await _api_get(f"/artists/{artist_id}")
    return data.get("resource", data)


async def search_by_isrc(isrc: str) -> dict | None:
    """Filter tracks by ISRC. Returns the first match or None."""
    data = await _api_get("/tracks", params={"filter[isrc]": isrc})
    items = data.get("data", [])
    return items[0].get("resource", items[0]) if items else None


async def search_by_upc(upc: str) -> dict | None:
    """Filter albums by barcode. Returns the first match or None."""
    data = await _api_get("/albums", params={"filter[barcodeId]": upc})
    items = data.get("data", [])
    return items[0].get("resource", items[0]) if items else None


async def search_artist(name: str) -> dict | None:
    """Search for an artist by name. Returns the first match or None."""
    data = await _api_get("/search", params={"query": name, "type": "ARTISTS", "limit": 1})
    items = data.get("artists", [])
    return items[0].get("resource", items[0]) if items else None


def extract_isrc(track: dict) -> str | None:
    return track.get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("barcodeId")


def extract_track_url(track: dict) -> str | None:
    tid = track.get("id")
    return f"https://tidal.com/track/{tid}" if tid else None


def extract_album_url(album: dict) -> str | None:
    aid = album.get("id")
    return f"https://tidal.com/album/{aid}" if aid else None


def extract_artist_url(artist: dict) -> str | None:
    aid = artist.get("id")
    return f"https://tidal.com/artist/{aid}" if aid else None


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    title = track.get("title")
    artists = track.get("artists", [])
    if artists:
        names = [a.get("name") for a in artists if a.get("name")]
        return title, ", ".join(names) if names else None
    return title, None
