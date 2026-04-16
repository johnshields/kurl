import httpx

from app.constants import CLIENT_TIMEOUT, DEEZER_API_BASE
from utils.logging import get_logger

logger = get_logger()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=CLIENT_TIMEOUT)
    return _client


def is_configured() -> bool:
    # Deezer public API requires no credentials.
    return True


async def _api_get(path: str, params: dict | None = None) -> dict:
    response = await _get_client().get(f"{DEEZER_API_BASE}{path}", params=params)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        logger.warning("Deezer API error on %s: %s", path, data["error"])
        return {}
    return data


async def get_track(track_id: str) -> dict:
    """GET /track/{id} -- returns track object including isrc."""
    return await _api_get(f"/track/{track_id}")


async def get_album(album_id: str) -> dict:
    """GET /album/{id} -- returns album object including upc."""
    return await _api_get(f"/album/{album_id}")


async def get_artist(artist_id: str) -> dict:
    """GET /artist/{id} -- returns artist name, picture, etc."""
    return await _api_get(f"/artist/{artist_id}")


async def search_by_isrc(isrc: str) -> dict | None:
    """Lookup track by ISRC (undocumented but widely used endpoint)."""
    data = await _api_get(f"/track/isrc:{isrc}")
    if not data or "id" not in data:
        return None
    return data


async def search_by_upc(upc: str) -> dict | None:
    """Search for an album by UPC via the search endpoint."""
    data = await _api_get("/search/album", params={"q": upc})
    items = data.get("data", [])
    # UPC match is not guaranteed by search; caller should verify.
    return items[0] if items else None


async def search_artist(name: str) -> dict | None:
    """Search for an artist by name. Returns the first match or None."""
    data = await _api_get("/search/artist", params={"q": name})
    items = data.get("data", [])
    return items[0] if items else None


def extract_isrc(track: dict) -> str | None:
    return track.get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("upc")


def extract_track_url(track: dict) -> str | None:
    return track.get("link")


def extract_album_url(album: dict) -> str | None:
    return album.get("link")


def extract_artist_url(artist: dict) -> str | None:
    return artist.get("link")


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    title = track.get("title")
    artist = track.get("artist", {}).get("name")
    return title, artist
