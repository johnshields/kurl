"""
Friends Controller
Friend-request graph: send, accept, list, remove. All operations are scoped
to the signed-in user; removal is idempotent and covers decline, cancel and
unfriend in one query.
"""

from db.db import execute, fetch_all, fetch_one
from db.queries import friends as queries
from db.queries import users as user_queries
from models.friend import public_friend
from utils.api_result import error_result
from utils.logging import get_logger
from utils.uid import gen_uid

logger = get_logger()


async def list_friends(db, user_uid: str) -> dict:
    accepted = await fetch_all(db, queries.LIST_ACCEPTED, user_uid, user_uid, user_uid)
    incoming = await fetch_all(db, queries.LIST_INCOMING, user_uid)
    outgoing = await fetch_all(db, queries.LIST_OUTGOING, user_uid)
    return {
        "status": "success",
        "data": {
            "friends": [public_friend(r) for r in accepted],
            "incoming": [public_friend(r) for r in incoming],
            "outgoing": [public_friend(r) for r in outgoing],
        },
    }


async def send_request(db, user_uid: str, data: dict) -> dict:
    username = (data.get("username") or "").strip()
    if not username:
        return error_result("INVALID_REQUEST", "Username required.")

    target = await fetch_one(db, user_queries.GET_BY_USERNAME, username)
    if not target:
        return error_result("NOT_FOUND", "No user with that username.")
    if target["uid"] == user_uid:
        return error_result("INVALID_REQUEST", "Cannot send a friend request to yourself.")

    existing = await fetch_one(
        db, queries.GET_BETWEEN, user_uid, target["uid"], target["uid"], user_uid
    )
    if existing:
        if existing["status"] == "accepted":
            return error_result("ALREADY_FRIENDS", "Already friends.")
        return error_result("REQUEST_EXISTS", "A friend request is already pending.")

    uid = gen_uid("FRN")
    await execute(db, queries.INSERT, uid, user_uid, target["uid"])
    logger.info("Friend request %s: %s -> %s", uid, user_uid, target["uid"])
    return {"status": "success", "message": "Friend request sent.", "data": {"uid": uid}}


async def accept_request(db, user_uid: str, friend_uid: str) -> dict:
    row = await fetch_one(db, queries.GET_BY_UID, friend_uid)
    if not row or row["addressee_uid"] != user_uid or row["status"] != "pending":
        return error_result("NOT_FOUND", "No pending request to accept.")

    await execute(db, queries.ACCEPT, friend_uid, user_uid)
    logger.info("Friend request %s accepted by %s", friend_uid, user_uid)
    return {"status": "success", "message": "Friend request accepted."}


async def remove(db, user_uid: str, friend_uid: str) -> dict:
    # Scoped to a participant in the query -- one path for decline, cancel and unfriend.
    await execute(db, queries.DELETE, friend_uid, user_uid, user_uid)
    logger.info("Friendship %s removed by %s", friend_uid, user_uid)
    return {"status": "success", "message": "Removed."}
