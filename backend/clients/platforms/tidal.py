import time
from urllib.parse import quote

import httpx

from app.config import settings
from app.constants import CLIENT_TIMEOUT, DEFAULT_COUNTRY, TIDAL_ACCEPT_HEADER, TIDAL_API_BASE, TIDAL_TOKEN_URL
from clients.platforms._oauth import fetch_client_credentials_token
from utils.canonical_url import build_album_url, build_artist_url, build_track_url
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

    _token, expires_in = await fetch_client_credentials_token(
        _get_client(),
        TIDAL_TOKEN_URL,
        settings.TIDAL_CLIENT_ID,
        settings.TIDAL_CLIENT_SECRET,
    )
    _token_expires_at = time.time() + expires_in
    logger.info("Tidal token refreshed, expires in %ss", expires_in)
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
    """GET /v2/tracks/{id} -- returns JSON:API track resource."""
    data = await _api_get(f"/tracks/{track_id}")
    return data.get("data", {})


async def get_album(album_id: str) -> dict:
    """GET /v2/albums/{id} -- returns JSON:API album resource."""
    data = await _api_get(f"/albums/{album_id}")
    return data.get("data", {})


async def get_artist(artist_id: str) -> dict:
    """GET /v2/artists/{id} -- returns JSON:API artist resource."""
    data = await _api_get(f"/artists/{artist_id}")
    return data.get("data", {})


async def search_by_isrc(isrc: str) -> dict | None:
    """Filter tracks by ISRC. Returns the first match or None."""
    data = await _api_get("/tracks", params={"filter[isrc]": isrc})
    items = data.get("data", [])
    return items[0] if items else None


async def search_by_upc(upc: str) -> dict | None:
    """Filter albums by barcode. Returns the first match or None."""
    data = await _api_get("/albums", params={"filter[barcodeId]": upc})
    items = data.get("data", [])
    return items[0] if items else None


async def search_artist(name: str) -> dict | None:
    """Search for an artist via free-text. Returns the first match or None."""
    return await _search_first(name, "artists")


async def search_track(title: str, artist: str) -> dict | None:
    """Search for a track via free-text. Returns the first match or None."""
    return await _search_first(f"{artist} {title}", "tracks")


async def _search_first(query: str, relation: str) -> dict | None:
    """Tidal search (v2) -- /searchresults/{query}?include={relation}.

    Returns the first resource of the requested type from the `included` array.
    """
    encoded = quote(query, safe="")
    data = await _api_get(f"/searchresults/{encoded}", params={"include": relation})
    for resource in data.get("included", []):
        if resource.get("type") == relation:
            return resource
    return None


def extract_isrc(track: dict) -> str | None:
    return track.get("attributes", {}).get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("attributes", {}).get("barcodeId")


def extract_track_url(track: dict) -> str | None:
    tid = track.get("id")
    return build_track_url("tidal", str(tid)) if tid else None


def extract_album_url(album: dict) -> str | None:
    aid = album.get("id")
    return build_album_url("tidal", str(aid)) if aid else None


def extract_artist_url(artist: dict) -> str | None:
    aid = artist.get("id")
    return build_artist_url("tidal", str(aid)) if aid else None


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    attrs = track.get("attributes", {})
    # v2 JSON:API: artists live in relationships/included, not inline on the resource.
    # For free-text search, include=tracks doesn't hydrate artists -- we only get the title.
    return attrs.get("title"), None


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    attrs = album.get("attributes", {})
    return attrs.get("title"), None


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("attributes", {}).get("name")
