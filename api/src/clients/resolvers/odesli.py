import asyncio

from app.config import settings
from app.constants import (
    ODESLI_BACKOFF_SECONDS,
    ODESLI_MAX_RETRIES,
    ODESLI_UNRELIABLE_SOURCES,
    ODESLI_UNSUPPORTED_TARGETS,
)
from clients._http import get_client
from utils.http.errors import ApiError
from utils.logging import get_logger

logger = get_logger()


def should_skip(source_platform: str | None, target_platform: str) -> bool:
    """True when Odesli will fail or has no data for this pair."""
    if target_platform in ODESLI_UNSUPPORTED_TARGETS:
        return True
    if source_platform and source_platform in ODESLI_UNRELIABLE_SOURCES:
        return True
    return False


def _get_client():
    return get_client("odesli", timeout=5.0)


async def _call(params: dict) -> dict:
    params = {**params, "userCountry": params.get("userCountry", "IE")}
    if settings.ODESLI_API_KEY:
        params["key"] = settings.ODESLI_API_KEY

    for attempt in range(ODESLI_MAX_RETRIES):
        response = await _get_client().get(settings.ODESLI_BASE_URL, params=params)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429 and attempt < ODESLI_MAX_RETRIES - 1:
            wait = ODESLI_BACKOFF_SECONDS[attempt]
            logger.warning("Odesli 429; retrying in %ss (attempt %s/%s)", wait, attempt + 1, ODESLI_MAX_RETRIES)
            await asyncio.sleep(wait)
            continue

        logger.warning(
            "Odesli returned %s for %s: %s",
            response.status_code,
            params,
            response.text[:500],
        )
        is_rate = response.status_code == 429
        detail = (
            "Rate limited by Odesli, try again shortly"
            if is_rate
            else f"Odesli API error ({response.status_code})"
        )
        raise ApiError(
            status_code=502,
            detail=detail,
            code="RATE_LIMITED" if is_rate else "ODESLI_ERROR",
        )

    raise ApiError(
        status_code=502,
        detail="Rate limited by Odesli, try again shortly",
        code="RATE_LIMITED",
    )


async def resolve_by_id(platform: str, track_id: str) -> dict:
    """Odesli lookup by platform + id."""
    logger.info("Calling Odesli: %s type=song id=%s", platform, track_id)
    return await _call({"platform": platform, "type": "song", "id": track_id})


async def resolve(url: str) -> dict:
    """Odesli lookup by URL."""
    logger.info("Calling Odesli: %s", url)
    return await _call({"url": url})


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
