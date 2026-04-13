import httpx
from fastapi import HTTPException

from app.config import settings
from app.constants import ERROR_MESSAGES

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def resolve(url: str) -> dict:
    params = {"url": url, "userCountry": "IE"}
    if settings.ODESLI_API_KEY:
        params["key"] = settings.ODESLI_API_KEY

    response = await _get_client().get(settings.ODESLI_BASE_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"{ERROR_MESSAGES['ODESLI_ERROR']} ({response.status_code})",
        )

    return response.json()


def extract_url(data: dict, platform: str) -> str | None:
    platform_data = data.get("linksByPlatform", {}).get(platform)
    if not platform_data:
        return None
    return platform_data.get("url")


def extract_metadata(data: dict) -> tuple[str | None, str | None]:
    entities = data.get("entitiesByUniqueId", {})
    for entity in entities.values():
        title = entity.get("title")
        artist = entity.get("artistName")
        if title:
            return title, artist
    return None, None
