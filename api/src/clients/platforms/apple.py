import time

import jwt

from app.config import settings
from app.constants import APPLE_API_BASE, APPLE_TOKEN_LIFETIME, DEFAULT_STOREFRONT
from clients.platforms._http import get_client
from clients.platforms._oauth import TokenCache

_tokens = TokenCache("Apple Music")


def _generate_token() -> str:
    """Generate an Apple Music developer JWT (ES256), cached until expiry."""
    if cached := _tokens.get_cached():
        return cached

    now = int(time.time())
    token = jwt.encode(
        {"iss": settings.APPLE_TEAM_ID, "iat": now, "exp": now + APPLE_TOKEN_LIFETIME},
        settings.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers={"alg": "ES256", "kid": settings.APPLE_KEY_ID},
    )
    return _tokens.store(token, APPLE_TOKEN_LIFETIME)


async def _api_get(path: str, params: dict | None = None) -> dict:
    token = _generate_token()
    response = await get_client("apple").get(
        f"{APPLE_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.APPLE_TEAM_ID and settings.APPLE_KEY_ID and settings.APPLE_PRIVATE_KEY)


async def get_track(track_id: str, storefront: str = DEFAULT_STOREFRONT) -> dict:
    """GET /v1/catalog/{storefront}/songs/{id}"""
    data = await _api_get(f"/catalog/{storefront}/songs/{track_id}")
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


async def search_track(title: str, artist: str, storefront: str = DEFAULT_STOREFRONT) -> dict | None:
    """Search for a track by title and artist. Returns the first match or None."""
    data = await _api_get(
        f"/catalog/{storefront}/search",
        params={"term": f"{artist} {title}", "types": "songs", "limit": 1},
    )
    results = data.get("results", {}).get("songs", {}).get("data", [])
    return results[0] if results else None


def extract_isrc(song: dict) -> str | None:
    return song.get("attributes", {}).get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("attributes", {}).get("upc")


def extract_track_url(track: dict) -> str | None:
    return track.get("attributes", {}).get("url")


def extract_album_url(album: dict) -> str | None:
    return album.get("attributes", {}).get("url")


def extract_artist_url(artist: dict) -> str | None:
    return artist.get("attributes", {}).get("url")


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    attrs = track.get("attributes", {})
    return attrs.get("name"), attrs.get("artistName")


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    attrs = album.get("attributes", {})
    return attrs.get("name"), attrs.get("artistName")


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("attributes", {}).get("name")
