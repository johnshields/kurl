"""
Auth Controller
Signup, login, and current-user logic for the (optional) account system.
"""

from app.config import settings
from app.constants import PLATFORMS
from db.db import execute, fetch_one
from db.queries import users as queries
from models.user import public_user, to_db_params
from utils.logging import get_logger
from utils.password import hash_password, verify_password
from utils.session import create_session_token
from utils.uid import gen_uid
from utils.username import generate_username, generate_username_with_suffix, is_valid_username

logger = get_logger()

# generate_username() collisions should be rare (large word pool) -- this is
# just a safety cap so signup can't loop forever if the table fills up.
_USERNAME_GEN_ATTEMPTS = 10


async def _unique_username(db) -> str:
    for _ in range(_USERNAME_GEN_ATTEMPTS):
        candidate = generate_username()
        if not await fetch_one(db, queries.GET_BY_USERNAME, candidate):
            return candidate
    # Exhausted retries -- add a short random suffix, still checked once.
    return generate_username_with_suffix()


async def signup(db, data: dict) -> dict:
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or "@" not in email:
        return {"status": "error", "code": "INVALID_EMAIL", "message": "Valid email required."}
    if len(password) < 8:
        return {"status": "error", "code": "WEAK_PASSWORD", "message": "Password must be at least 8 characters."}

    existing = await fetch_one(db, queries.GET_BY_EMAIL, email)
    if existing:
        return {"status": "error", "code": "EMAIL_TAKEN", "message": "Email already registered."}

    uid = gen_uid("USR")
    username = await _unique_username(db)
    await execute(db, queries.INSERT, *to_db_params(uid, email, username, hash_password(password)))

    token = create_session_token(uid, settings.SESSION_SECRET)
    logger.info("Signed up: %s (%s)", uid, username)
    return {
        "status": "success",
        "message": "Account created.",
        "data": {
            "token": token,
            "user": {"uid": uid, "email": email, "username": username, "preferredPlatform": None},
        },
    }


async def login(db, data: dict) -> dict:
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    row = await fetch_one(db, queries.GET_BY_EMAIL, email)
    if not row or not verify_password(password, row["password_hash"]):
        return {"status": "error", "code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}

    token = create_session_token(row["uid"], settings.SESSION_SECRET)
    logger.info("Logged in: %s", row["uid"])
    return {
        "status": "success",
        "message": "Logged in.",
        "data": {"token": token, "user": public_user(row)},
    }


async def get_me(db, user_uid: str) -> dict:
    row = await fetch_one(db, queries.GET_BY_UID, user_uid)
    if not row:
        return {"status": "error", "code": "NOT_FOUND", "message": "User not found."}
    return {"status": "success", "data": public_user(row)}


async def update_profile(db, user_uid: str, data: dict) -> dict:
    """Partial update -- applies whichever of username/preferredPlatform are present."""
    if "username" in data:
        username = (data.get("username") or "").strip()
        if not is_valid_username(username):
            return {
                "status": "error",
                "code": "INVALID_USERNAME",
                "message": "Username must be 3-40 characters (letters, numbers, - or _).",
            }
        existing = await fetch_one(db, queries.GET_BY_USERNAME, username)
        if existing and existing["uid"] != user_uid:
            return {"status": "error", "code": "USERNAME_TAKEN", "message": "Username already taken."}
        await execute(db, queries.UPDATE_USERNAME, username, user_uid)
        logger.info("Updated username for %s: %s", user_uid, username)

    if "preferredPlatform" in data:
        platform = data.get("preferredPlatform")
        if platform is not None and platform not in PLATFORMS:
            return {"status": "error", "code": "UNKNOWN_PLATFORM", "message": "Unknown platform."}
        await execute(db, queries.UPDATE_PREFERRED_PLATFORM, platform, user_uid)
        logger.info("Updated preferred platform for %s: %s", user_uid, platform)

    row = await fetch_one(db, queries.GET_BY_UID, user_uid)
    return {"status": "success", "message": "Profile updated.", "data": public_user(row)}
