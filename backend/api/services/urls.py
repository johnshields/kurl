import hashlib
import json

from fastapi import HTTPException

from app.constants import ERROR_MESSAGES, PLATFORMS
from clients import cache, odesli
from utils.logging import get_logger
from utils.responses import success
from utils.search_url import build_search_url
from utils.url import normalise_url
from utils.url_parser import parse_track
from utils.wrap_route import wrap_route

logger = get_logger()


@wrap_route("Resolve")
async def resolve_url(url: str, target_platform: str):
    """Resolve a streaming URL to the target platform via Odesli."""
    if target_platform not in PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"{ERROR_MESSAGES['UNKNOWN_PLATFORM']}: {target_platform}",
        )

    url = normalise_url(url)
    logger.info("Resolving %s -> %s", url, target_platform)

    cache_key = hashlib.md5(
        f"{url}{target_platform}".encode()
    ).hexdigest()

    cached = await cache.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        logger.info("Cache hit: %s - %s", data.get("artist"), data.get("title"))
        return success("URL resolved from cache", data)

    parsed = parse_track(url)
    if parsed:
        logger.info("Parsed track: %s id=%s", parsed.platform, parsed.track_id)
        odesli_data = await odesli.resolve_by_id(parsed.platform, parsed.track_id)
    else:
        odesli_data = await odesli.resolve(url)

    resolved_url = odesli.extract_url(odesli_data, target_platform)
    title, artist = odesli.extract_metadata(odesli_data)
    via = "direct"

    if not resolved_url:
        available = sorted(odesli_data.get("linksByPlatform", {}).keys())
        logger.warning(
            "No %s URL; Odesli returned platforms: %s", target_platform, available
        )
        resolved_url = build_search_url(target_platform, title, artist)
        if not resolved_url:
            raise HTTPException(
                status_code=404,
                detail=f"{ERROR_MESSAGES['PLATFORM_NOT_FOUND']} ({target_platform})",
            )
        via = "search"
        logger.info("Using search fallback for %s: %s", target_platform, resolved_url)
    else:
        logger.info("Resolved: %s - %s -> %s", artist, title, resolved_url)

    result = {
        "title": title,
        "artist": artist,
        "resolved_url": resolved_url,
        "platform": target_platform,
        "via": via,
    }

    await cache.set(cache_key, json.dumps(result))

    result["cached"] = False
    return success("URL resolved", result)
