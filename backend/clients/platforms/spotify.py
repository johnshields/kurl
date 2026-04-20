from app.config import settings
from app.constants import SPOTIFY_API_BASE, SPOTIFY_TOKEN_URL
from clients.platforms._http import get_client
from clients.platforms._oauth import TokenCache

_tokens = TokenCache("Spotify")


async def _get_token() -> str:
    return await _tokens.fetch_via_oauth(
        get_client("spotify"),
        SPOTIFY_TOKEN_URL,
        settings.SPOTIFY_CLIENT_ID,
        settings.SPOTIFY_CLIENT_SECRET,
    )


async def _api_get(path: str, params: dict | None = None) -> dict:
    token = await _get_token()
    response = await get_client("spotify").get(
        f"{SPOTIFY_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


def is_configured() -> bool:
    return bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)


async def get_track(track_id: str) -> dict:
    """GET /v1/tracks/{id} -- returns full track object including external_ids.isrc."""
    return await _api_get(f"/tracks/{track_id}")


async def get_album(album_id: str) -> dict:
    """GET /v1/albums/{id} -- returns full album object including external_ids.upc."""
    return await _api_get(f"/albums/{album_id}")


async def get_artist(artist_id: str) -> dict:
    """GET /v1/artists/{id} -- returns artist name, popularity, genres."""
    return await _api_get(f"/artists/{artist_id}")


async def search_by_isrc(isrc: str) -> dict | None:
    """Search for a track by ISRC. Returns the first match or None."""
    data = await _api_get("/search", params={"q": f"isrc:{isrc}", "type": "track", "limit": 1})
    items = data.get("tracks", {}).get("items", [])
    return items[0] if items else None


async def search_by_upc(upc: str) -> dict | None:
    """Search for an album by UPC. Returns the first match or None."""
    data = await _api_get("/search", params={"q": f"upc:{upc}", "type": "album", "limit": 1})
    items = data.get("albums", {}).get("items", [])
    return items[0] if items else None


async def search_artist(name: str) -> dict | None:
    """Search for an artist by name. Returns the first match or None."""
    data = await _api_get("/search", params={"q": f"artist:{name}", "type": "artist", "limit": 1})
    items = data.get("artists", {}).get("items", [])
    return items[0] if items else None


async def search_track(title: str, artist: str) -> dict | None:
    """Search for a track by title and artist. Returns the first match or None."""
    query = f"track:{title} artist:{artist}"
    data = await _api_get("/search", params={"q": query, "type": "track", "limit": 1})
    items = data.get("tracks", {}).get("items", [])
    return items[0] if items else None


def extract_isrc(track: dict) -> str | None:
    return track.get("external_ids", {}).get("isrc")


def extract_upc(album: dict) -> str | None:
    return album.get("external_ids", {}).get("upc")


def extract_track_url(track: dict) -> str | None:
    return track.get("external_urls", {}).get("spotify")


def extract_album_url(album: dict) -> str | None:
    return album.get("external_urls", {}).get("spotify")


def extract_artist_url(artist: dict) -> str | None:
    return artist.get("external_urls", {}).get("spotify")


def extract_metadata(track: dict) -> tuple[str | None, str | None]:
    title = track.get("name")
    artists = [a.get("name") for a in track.get("artists", []) if a.get("name")]
    return title, ", ".join(artists) if artists else None


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    title = album.get("name")
    artists = [a.get("name") for a in album.get("artists", []) if a.get("name")]
    return title, ", ".join(artists) if artists else None


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("name")
