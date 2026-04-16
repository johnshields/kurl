import hashlib
import json

from fastapi import HTTPException

from app.constants import ERROR_MESSAGES, PLATFORMS
from clients import cache, metadata, odesli
from utils.kurler import kurl as kurl_direct
from utils.logging import get_logger
from utils.responses import success
from utils.search_url import build_search_url
from utils.short_links import is_short_link, resolve_short_link
from utils.url import normalise_url
from utils.url_parser import is_search_url, parse_music_url, parse_track
from utils.wrap_route import wrap_route

logger = get_logger()


@wrap_route("Kurl")
async def kurl(url: str, target_platform: str):
    """Kurl a streaming URL to the target platform.

    Resolution order:
    1. Direct ISRC/UPC/name via platform APIs (fast path)
    2. Odesli by-id or by-url (fallback)
    3. Metadata scraping + search URL (last resort)
    """
    if target_platform not in PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"{ERROR_MESSAGES['UNKNOWN_PLATFORM']}: {target_platform}",
        )

    url = normalise_url(url)

    # Follow platform short links (spotify.link, dzr.page.link) to their canonical URL.
    if is_short_link(url):
        url = normalise_url(await resolve_short_link(url))

    logger.info("Kurling %s -> %s", url, target_platform)

    if is_search_url(url):
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES["SEARCH_URL"])

    cache_key = hashlib.md5(f"{url}{target_platform}".encode()).hexdigest()

    cached = await cache.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        logger.info("Cache hit: %s - %s", data.get("artist"), data.get("title"))
        return success("Kurled from cache", data)

    # Try direct ISRC/UPC resolution via platform APIs first.
    parsed_full = parse_music_url(url)
    if parsed_full:
        logger.info("Parsed: %s %s id=%s", parsed_full.platform, parsed_full.entity_type, parsed_full.id)
        try:
            match = await kurl_direct(parsed_full, target_platform)
            if match:
                logger.info("Direct kurl: %s - %s -> %s (via %s)", match.artist, match.title, match.url, match.via)
                result = {
                    "title": match.title,
                    "artist": match.artist,
                    "resolved_url": match.url,
                    "platform": target_platform,
                    "via": match.via,
                }
                await cache.set(cache_key, json.dumps(result))
                result["cached"] = False
                return success("Kurled", result)
        except Exception as e:
            logger.warning("Direct kurl failed, falling back to Odesli: %s", e)

    # Odesli fallback.
    parsed = parse_track(url)
    odesli_data: dict = {}
    odesli_error: HTTPException | None = None

    try:
        if parsed:
            logger.info("Parsed track: %s id=%s", parsed.platform, parsed.track_id)
            odesli_data = await odesli.resolve_by_id(parsed.platform, parsed.track_id)
        else:
            odesli_data = await odesli.resolve(url)
    except HTTPException as e:
        odesli_error = e
        logger.warning("Odesli unavailable (%s): %s", e.status_code, e.detail)

    resolved_url = odesli.extract_url(odesli_data, target_platform) if odesli_data else None
    title, artist = odesli.extract_metadata(odesli_data) if odesli_data else (None, None)
    via = "direct"

    if resolved_url:
        logger.info("Kurled: %s - %s -> %s", artist, title, resolved_url)
    else:
        if odesli_data:
            available = sorted(odesli_data.get("linksByPlatform", {}).keys())
            logger.warning("No %s URL; Odesli returned platforms: %s", target_platform, available)

        # If Odesli didn't give us metadata, try scraping the source URL directly.
        if (not title or not artist) and parsed:
            scraped_title, scraped_artist = await metadata.fetch_metadata(parsed, url)
            title = title or scraped_title
            artist = artist or scraped_artist
            logger.info("Scraped metadata: %s - %s", artist, title)

        resolved_url = build_search_url(target_platform, title, artist)
        if not resolved_url:
            if odesli_error:
                raise odesli_error
            raise HTTPException(
                status_code=404,
                detail=f"{ERROR_MESSAGES['PLATFORM_NOT_FOUND']} ({target_platform})",
            )
        via = "search"
        logger.info("Using search fallback for %s: %s", target_platform, resolved_url)

    result = {
        "title": title,
        "artist": artist,
        "resolved_url": resolved_url,
        "platform": target_platform,
        "via": via,
    }

    await cache.set(cache_key, json.dumps(result))

    result["cached"] = False
    return success("Kurled", result)
