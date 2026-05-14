from urllib.parse import quote

from app.config import settings
from app.constants import DEFAULT_COUNTRY, TIDAL_ACCEPT_HEADER, TIDAL_API_BASE, TIDAL_TOKEN_URL
from clients.platforms._http import get_client
from clients.platforms._oauth import TokenCache
from utils.canonical_url import build_album_url, build_artist_url, build_track_url
from utils.logging import get_logger

logger = get_logger()

_tokens = TokenCache("Tidal")


async def _get_token() -> str:
    return await _tokens.fetch_via_oauth(
        get_client("tidal"),
        TIDAL_TOKEN_URL,
        settings.TIDAL_CLIENT_ID,
        settings.TIDAL_CLIENT_SECRET,
    )


async def _api_get(path: str, params: dict | None = None) -> dict:
    token = await _get_token()
    params = {**(params or {}), "countryCode": (params or {}).get("countryCode", DEFAULT_COUNTRY)}
    response = await get_client("tidal").get(
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

    Tidal returns JSON:API: `data.relationships.{relation}.data[]` is the ordered
    list of `{type, id}` pointers; `included[]` holds the full resources. Return
    the first resource in relevance order.
    """
    encoded = quote(query, safe="")
    data = await _api_get(f"/searchResults/{encoded}", params={"include": relation})

    refs = data.get("data", {}).get("relationships", {}).get(relation, {}).get("data", [])
    if not refs:
        return None
    first_id = refs[0].get("id")

    for resource in data.get("included", []):
        if resource.get("type") == relation and resource.get("id") == first_id:
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
    # For free-text search, include=tracks doesn't hydrate artists -- only the title is returned.
    return attrs.get("title"), None


def extract_album_metadata(album: dict) -> tuple[str | None, str | None]:
    attrs = album.get("attributes", {})
    return attrs.get("title"), None


def extract_artist_name(artist: dict) -> str | None:
    return artist.get("attributes", {}).get("name")
