"""
Messages Controller
Direct messages between friends: send (text and/or an attached kurl), list
threads, read a thread, delete a message. Sending requires an accepted
friendship; a thread is created on the first message to a new recipient.
"""

import json

from db.db import execute, fetch_all, fetch_one
from db.queries import friends as friend_queries
from db.queries import messages as queries
from db.queries import threads as thread_queries
from db.queries import users as user_queries
from models.message import public_message
from models.thread import thread_header, thread_summary
from utils.api_result import error_result
from utils.logging import get_logger
from utils.uid import gen_uid

logger = get_logger()

_MAX_BODY = 2000


def _pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


def _is_participant(row: dict, viewer_uid: str) -> bool:
    return viewer_uid in (row["user_a_uid"], row["user_b_uid"])


def _other_participant(row: dict, viewer_uid: str) -> str:
    return row["user_b_uid"] if row["user_a_uid"] == viewer_uid else row["user_a_uid"]


async def _mark_read(db, thread_row: dict, viewer_uid: str) -> None:
    query = (
        thread_queries.MARK_READ_A
        if thread_row["user_a_uid"] == viewer_uid
        else thread_queries.MARK_READ_B
    )
    await execute(db, query, thread_row["uid"])


async def list_threads(db, user_uid: str) -> dict:
    rows = await fetch_all(
        db, thread_queries.LIST_FOR_USER, user_uid, user_uid, user_uid, user_uid, user_uid
    )
    return {"status": "success", "data": [thread_summary(r) for r in rows]}


async def get_thread(db, user_uid: str, thread_uid: str) -> dict:
    thread = await fetch_one(db, thread_queries.GET_BY_UID, thread_uid)
    if not thread or not _is_participant(thread, user_uid):
        return error_result("NOT_FOUND", "Thread not found.")

    other = await fetch_one(db, user_queries.GET_BY_UID, _other_participant(thread, user_uid))
    messages = await fetch_all(db, queries.LIST_FOR_THREAD, thread_uid)
    await _mark_read(db, thread, user_uid)

    return {
        "status": "success",
        "data": {
            "thread": thread_header(thread, other, user_uid),
            "messages": [public_message(m) for m in messages],
        },
    }


async def mark_read(db, user_uid: str, thread_uid: str) -> dict:
    thread = await fetch_one(db, thread_queries.GET_BY_UID, thread_uid)
    if not thread or not _is_participant(thread, user_uid):
        return error_result("NOT_FOUND", "Thread not found.")
    await _mark_read(db, thread, user_uid)
    return {"status": "success", "message": "Marked read."}


async def send(db, user_uid: str, data: dict) -> dict:
    body = (data.get("body") or "").strip() or None
    kurl = data.get("kurl") or None

    if body is None and kurl is None:
        return error_result("EMPTY_MESSAGE", "A message needs text or an attached kurl.")
    if body and len(body) > _MAX_BODY:
        return error_result("BODY_TOO_LONG", f"Message must be {_MAX_BODY} characters or fewer.")
    if kurl is not None and not isinstance(kurl, dict):
        return error_result("INVALID_REQUEST", "kurl must be an object.")

    thread, other_uid, err = await _resolve_thread(db, user_uid, data)
    if err:
        return err

    if not await fetch_one(
        db, friend_queries.ARE_FRIENDS, user_uid, other_uid, other_uid, user_uid
    ):
        return error_result("NOT_FRIENDS", "You can only message friends.")

    if thread is None:
        thread = await _create_thread(db, user_uid, other_uid)

    kurl_recipient = await _resolve_for_recipient(db, other_uid, kurl) if kurl is not None else None

    uid = gen_uid("MSG")
    await execute(
        db,
        queries.INSERT,
        uid,
        thread["uid"],
        user_uid,
        body,
        json.dumps(kurl) if kurl is not None else None,
        json.dumps(kurl_recipient) if kurl_recipient is not None else None,
    )
    await execute(db, thread_queries.TOUCH, thread["uid"])
    await _mark_read(db, thread, user_uid)
    logger.info("Message %s in thread %s from %s", uid, thread["uid"], user_uid)

    row = await fetch_one(db, queries.GET_BY_UID, uid)
    return {"status": "success", "message": "Sent.", "data": public_message(row)}


async def delete_message(db, user_uid: str, message_uid: str) -> dict:
    # Scoped to the sender in the query -- deleting is idempotent either way.
    await execute(db, queries.DELETE, message_uid, user_uid)
    logger.info("Message %s deleted by %s", message_uid, user_uid)
    return {"status": "success", "message": "Deleted."}


async def _resolve_thread(db, user_uid: str, data: dict):
    """Returns (thread_or_None, other_uid, error) -- thread is None when the pair has no thread yet."""
    thread_uid = data.get("threadUid")
    if thread_uid:
        thread = await fetch_one(db, thread_queries.GET_BY_UID, thread_uid)
        if not thread or not _is_participant(thread, user_uid):
            return None, None, error_result("NOT_FOUND", "Thread not found.")
        return thread, _other_participant(thread, user_uid), None

    target = None
    if data.get("toUid"):
        target = await fetch_one(db, user_queries.GET_BY_UID, data["toUid"])
    elif data.get("toUsername"):
        target = await fetch_one(db, user_queries.GET_BY_USERNAME, data["toUsername"])
    if not target:
        return None, None, error_result("NOT_FOUND", "Recipient not found.")
    if target["uid"] == user_uid:
        return None, None, error_result("INVALID_REQUEST", "Cannot message yourself.")

    a, b = _pair(user_uid, target["uid"])
    thread = await fetch_one(db, thread_queries.GET_BY_PAIR, a, b)
    return thread, target["uid"], None


async def _create_thread(db, user_uid: str, other_uid: str) -> dict:
    a, b = _pair(user_uid, other_uid)
    uid = gen_uid("THR")
    await execute(db, thread_queries.INSERT, uid, a, b)
    logger.info("Thread %s created for %s + %s", uid, a, b)
    return await fetch_one(db, thread_queries.GET_BY_UID, uid)


async def _resolve_for_recipient(db, recipient_uid: str, kurl: dict) -> dict | None:
    """Re-resolve an attached kurl into the recipient's preferred platform.
    Best-effort -- any miss returns None and the sender snapshot stands."""
    source_url = kurl.get("source_url")
    if not source_url:
        return None

    recipient = await fetch_one(db, user_queries.GET_BY_UID, recipient_uid)
    pref = recipient.get("preferred_platform") if recipient else None
    if not pref or pref == kurl.get("platform"):
        return None

    from api.services.urls import resolve

    try:
        result = await resolve(source_url, pref, db=db, save_history=False)
    except Exception as e:
        logger.warning("Recipient re-resolve failed (%s -> %s): %s", source_url, pref, e)
        return None

    return {
        "target_url": result["resolved_url"],
        "platform": result["platform"],
        "via": result["via"],
    }
