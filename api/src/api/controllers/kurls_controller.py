"""
Kurls Controller
Record and list a signed-in user's saved kurl history. Recording is always
best-effort -- called from the public kurl flow, must never fail the
anonymous-by-default kurl response.
"""

from db.db import execute, fetch_all
from db.queries import kurls as queries
from models.kurl_record import from_db_row, to_db_params
from utils.logging import get_logger
from utils.uid import gen_uid

logger = get_logger()


async def record_kurl(
    db,
    user_uid: str,
    *,
    source_url: str,
    target_url: str,
    platform: str,
    via: str,
    title: str | None,
    artist: str | None,
) -> None:
    uid = gen_uid("KRL")
    try:
        await execute(
            db,
            queries.INSERT,
            *to_db_params(uid, user_uid, source_url, target_url, platform, via, title, artist),
        )
        logger.info("Recorded kurl %s for %s", uid, user_uid)
    except Exception as e:
        logger.warning("Failed to record kurl for %s: %s", user_uid, e)


async def list_kurls(db, user_uid: str) -> dict:
    rows = await fetch_all(db, queries.LIST_FOR_USER, user_uid)
    return {"status": "success", "data": [from_db_row(r) for r in rows]}


async def delete_kurl(db, user_uid: str, kurl_uid: str) -> dict:
    # Scoped to owner in the query itself -- deleting is idempotent either way.
    await execute(db, queries.DELETE, kurl_uid, user_uid)
    logger.info("Deleted kurl %s for %s", kurl_uid, user_uid)
    return {"status": "success", "message": "Kurl deleted."}
