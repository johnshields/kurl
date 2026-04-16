import time

import httpx
import jwt

from app.config import settings
from app.constants import APPLE_API_BASE, APPLE_TOKEN_LIFETIME, CLIENT_TIMEOUT, DEFAULT_STOREFRONT
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


def _generate_token() -> str:
    """Generate an Apple Music developer JWT (ES256)."""
    global _token, _token_expires_at

    if _token and time.time() < _token_expires_at - 60:
        return _token

    now = int(time.time())
    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": now,
        "exp": now + APPLE_TOKEN_LIFETIME,
    }
    headers = {
        "alg": "ES256",
        "kid": settings.APPLE_KEY_ID,
    }

    _token = jwt.encode(payload, settings.APPLE_PRIVATE_KEY, algorithm="ES256", headers=headers)
    _token_expires_at = now + APPLE_TOKEN_LIFETIME
    logger.info("Apple Music token generated, expires in %ss", APPLE_TOKEN_LIFETIME)
    return _token


async def _api_get(path: str, params: dict | None = None) -> dict:
    token = _generate_token()
    response = await _get_client().get(
        f"{APPLE_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.APPLE_TEAM_ID and settings.APPLE_KEY_ID and settings.APPLE_PRIVATE_KEY)


async def get_song(song_id: str, storefront: str = DEFAULT_STOREFRONT) -> dict:
    """GET /v1/catalog/{storefront}/songs/{id}"""
    data = await _api_get(f"/catalog/{storefront}/songs/{song_id}")
    items = data.get("data", [])
    return items[0] if items else {}


async def get_album(album_id: str, storefront: str = DEFAULT_STOREFRONT) -> dict:
    """GET /v1/catalog/{storefront}/albums/{id}"""
    data = await _api_get(f"/catalog/{storefront}/albums/{album_id}")
    items = data.get("data", [])
    return items[0] if items else {}


async def get_artist(artist_id: str, storefront: str = DEFAULT_STOREFRONT) -> dict:
    """GET /v1/catalog/{storefront}/artists/{id}"""
    data = await _api_get(f"/catalog/{storefront}/artists/{artist_id}")
    items = data.get("data", [])
    return items[0] if items else {}


async def search_by_isrc(isrc: str, storefront: str = DEFAULT_STOREFRONT) -> dict | None:
    """Filter songs by ISRC. Returns the first match or None."""
    data = await _api_get(
        f"/catalog/{storefront}/songs",
        params={"filter[isrc]": isrc},
    )
    items = data.get("data", [])
    return items[0] if items else None


async def search_by_upc(upc: str, storefront: str = DEFAULT_STOREFRONT) -> dict | None:
    """Filter albums by UPC. Returns the first match or None."""
    data = await _api_get(
        f"/catalog/{storefront}/albums",
        params={"filter[upc]": upc},
    )
    items = data.get("data", [])
    return items[0] if items else None


async def search_artist(name: str, storefront: str = DEFAULT_STOREFRONT) -> dict | None:
    """Search for an artist by name. Returns the first match or None."""
    data = await _api_get(
        f"/catalog/{storefront}/search",
        params={"term": name, "types": "artists", "limit": 1},
    )
    results = data.get("results", {}).get("artists", {}).get("data", [])
    return results[0] if results else None


def extract_isrc(song: dict) -> str | None:
    return song.get("attributes", {}).get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("attributes", {}).get("upc")


def extract_song_url(song: dict) -> str | None:
    return song.get("attributes", {}).get("url")


def extract_album_url(album: dict) -> str | None:
    return album.get("attributes", {}).get("url")


def extract_artist_url(artist: dict) -> str | None:
    return artist.get("attributes", {}).get("url")


def extract_metadata(song: dict) -> tuple[str | None, str | None]:
    attrs = song.get("attributes", {})
    return attrs.get("name"), attrs.get("artistName")
