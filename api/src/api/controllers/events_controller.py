"""
Events Controller
Business logic for analytics events against D1 (SQLite).
"""

from datetime import datetime, timedelta

from db.db import execute, fetch_all
from db.queries import events as queries
from models.event import from_db_row, to_db_params
from utils.logging import get_logger
from utils.uid import gen_uid

logger = get_logger()

BOT_PATTERNS = [
    "bot", "crawler", "spider", "headlesschrome", "ahrefsbot",
    "googlebot", "bingbot", "slurp", "duckduckbot",
    "facebookexternalhit", "semrushbot",
]


def _is_bot(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    return any(p in ua for p in BOT_PATTERNS)


async def create_event(db, data: dict, meta: dict) -> dict:
    if _is_bot(meta.get("userAgent", "")):
        return {"status": "success", "message": "Ignored.", "uid": None}

    uid = gen_uid("EVT")
    params = to_db_params(data, uid, meta)
    await execute(db, queries.INSERT, *params)

    logger.info("Recorded event: %s (%s)", uid, data.get("type", ""))
    return {"status": "success", "message": "Event recorded.", "uid": uid}


def _since(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


async def get_summary(db, days: int = 7) -> dict:
    since = _since(days)

    by_type = await fetch_all(db, queries.SUMMARY_BY_TYPE, since)
    top_platforms = await fetch_all(db, queries.TOP_PLATFORMS, since)
    countries = await fetch_all(db, queries.COUNTRY_BREAKDOWN, since)
    match_quality = await fetch_all(db, queries.MATCH_QUALITY, since)
    recent = await fetch_all(db, queries.RECENT)

    logger.info("Fetched summary for last %d days", days)

    return {
        "days": days,
        "since": since,
        "totals": {row["type"]: row["count"] for row in by_type},
        "topPlatforms": [{"platform": r["platform"], "count": r["count"]} for r in top_platforms],
        "countries": [{"country": r["country"], "count": r["count"]} for r in countries],
        "matchQuality": [
            {
                "platform": r["platform"],
                "exact": r["exact_count"],
                "approx": r["approx_count"],
                "total": r["total"],
            }
            for r in match_quality
        ],
        "recent": [from_db_row(r) for r in recent],
    }


async def get_approx_pairs(db, days: int = 7) -> dict:
    since = _since(days)
    rows = await fetch_all(db, queries.APPROX_PAIRS, since)
    logger.info("Fetched approx pairs for last %d days", days)
    return {
        "days": days,
        "since": since,
        "pairs": [
            {"sourceUrl": r["source_url"], "platform": r["platform"], "misses": r["misses"]}
            for r in rows
        ],
    }
