"""
Auth Controller
Signup, login, and current-user logic for the (optional) account system.
"""

from app.config import settings
from app.constants import APP_BASE_URL, EMAIL_FROM, PLATFORMS
from clients import email as email_client
from db.db import execute, fetch_one
from db.queries import users as queries
from models.user import public_user, to_db_params
from utils.api_result import error_result
from utils.auth.auth_validation import normalise_email, weak_password_error
from utils.auth.email_verification import create_verification_token, decode_verification_token
from utils.auth.password import hash_password, verify_password
from utils.auth.password_reset import create_reset_token, decode_reset_token, matches_current_password
from utils.auth.session import create_session_token
from utils.auth.username import is_valid_username, unique_username
from utils.logging import get_logger
from utils.uid import gen_uid

logger = get_logger()


async def _send_verification_email(uid: str, email: str) -> None:
    token = create_verification_token(uid, settings.SESSION_SECRET)
    link = f"{APP_BASE_URL}/settings?verify={token}"
    await email_client.send(
        to=email,
        from_address=EMAIL_FROM,
        subject="Verify your kurl email",
        html=f'<p>Verify your kurl email:</p><p><a href="{link}">{link}</a></p><p>This link expires in 24 hours.</p>',
        text=f"Verify your kurl email: {link}\n\nThis link expires in 24 hours.",
    )
    logger.info("Sent verification email to %s", uid)


async def signup(db, data: dict) -> dict:
    email = normalise_email(data.get("email"))
    password = data.get("password") or ""

    if not email or "@" not in email:
        return error_result("INVALID_EMAIL", "Valid email required.")
    if weak := weak_password_error(password):
        return weak

    existing = await fetch_one(db, queries.GET_BY_EMAIL, email)
    if existing:
        return error_result("EMAIL_TAKEN", "Email already registered.")

    uid = gen_uid("USR")
    username = await unique_username(db)
    await execute(db, queries.INSERT, *to_db_params(uid, email, username, hash_password(password)))
    await _send_verification_email(uid, email)

    token = create_session_token(uid, settings.SESSION_SECRET)
    logger.info("Signed up: %s (%s)", uid, username)
    return {
        "status": "success",
        "message": "Account created.",
        "data": {
            "token": token,
            "user": {
                "uid": uid,
                "email": email,
                "username": username,
                "preferredPlatform": None,
                "emailVerified": False,
            },
        },
    }


async def login(db, data: dict) -> dict:
    email = normalise_email(data.get("email"))
    password = data.get("password") or ""

    row = await fetch_one(db, queries.GET_BY_EMAIL, email)
    if not row or not verify_password(password, row["password_hash"]):
        return error_result("INVALID_CREDENTIALS", "Invalid email or password.")

    token = create_session_token(row["uid"], settings.SESSION_SECRET)
    logger.info("Logged in: %s", row["uid"])
    return {
        "status": "success",
        "message": "Logged in.",
        "data": {"token": token, "user": public_user(row)},
    }


async def forgot_password(db, data: dict) -> dict:
    """Always succeeds -- avoids leaking which emails are registered."""
    email = normalise_email(data.get("email"))
    if email:
        row = await fetch_one(db, queries.GET_BY_EMAIL, email)
        if row:
            token = create_reset_token(row["uid"], row["password_hash"], settings.SESSION_SECRET)
            link = f"{APP_BASE_URL}/settings?reset={token}"
            await email_client.send(
                to=email,
                from_address=EMAIL_FROM,
                subject="Reset your kurl password",
                html=f'<p>Reset your kurl password:</p><p><a href="{link}">{link}</a></p>'
                f"<p>This link expires in 30 minutes. If you didn't request this, ignore this email.</p>",
                text=f"Reset your kurl password: {link}\n\n"
                "This link expires in 30 minutes. If you didn't request this, ignore this email.",
            )
            logger.info("Sent password reset email to %s", row["uid"])
    return {"status": "success", "message": "If that email has an account, a reset link has been sent.", "data": {}}


async def reset_password(db, data: dict) -> dict:
    token = data.get("token") or ""
    password = data.get("password") or ""

    if weak := weak_password_error(password):
        return weak

    decoded = decode_reset_token(token, settings.SESSION_SECRET)
    if not decoded:
        return error_result("INVALID_TOKEN", "Reset link is invalid or expired.")
    uid, fingerprint = decoded

    row = await fetch_one(db, queries.GET_BY_UID, uid)
    if not row or not matches_current_password(fingerprint, row["password_hash"]):
        return error_result("INVALID_TOKEN", "Reset link is invalid or expired.")

    await execute(db, queries.UPDATE_PASSWORD, hash_password(password), uid)
    token = create_session_token(uid, settings.SESSION_SECRET)
    logger.info("Password reset for %s", uid)
    return {
        "status": "success",
        "message": "Password updated.",
        "data": {"token": token, "user": public_user(row)},
    }


async def verify_email(db, data: dict) -> dict:
    uid = decode_verification_token(data.get("token") or "", settings.SESSION_SECRET)
    if not uid:
        return error_result("INVALID_TOKEN", "Verification link is invalid or expired.")

    row = await fetch_one(db, queries.GET_BY_UID, uid)
    if not row:
        return error_result("NOT_FOUND", "Account not found.")

    if not row.get("email_verified_at"):
        await execute(db, queries.UPDATE_EMAIL_VERIFIED, uid)
        logger.info("Verified email for %s", uid)
    return {"status": "success", "message": "Email verified.", "data": {}}


async def resend_verification(db, user_uid: str) -> dict:
    row = await fetch_one(db, queries.GET_BY_UID, user_uid)
    if not row or not row["email"]:
        return error_result("NOT_FOUND", "Account not found.")
    if row.get("email_verified_at"):
        return {"status": "success", "message": "Email already verified."}

    await _send_verification_email(user_uid, row["email"])
    return {"status": "success", "message": "Verification email sent."}


async def get_me(db, user_uid: str) -> dict:
    row = await fetch_one(db, queries.GET_BY_UID, user_uid)
    if not row:
        # Session token is valid but its user is gone -- treat as an invalid
        # session so the client clears it, not a lookup miss.
        return error_result("AUTH_REQUIRED", "Login required.")
    return {"status": "success", "data": public_user(row)}


async def update_profile(db, user_uid: str, data: dict) -> dict:
    """Partial update -- applies whichever of email/username/preferredPlatform/password are present."""
    if "email" in data:
        email = normalise_email(data.get("email"))
        if not email or "@" not in email:
            return error_result("INVALID_EMAIL", "Valid email required.")

        current = await fetch_one(db, queries.GET_BY_UID, user_uid)
        if current and current["email"]:
            return error_result("EMAIL_ALREADY_SET", "Email already set.")

        existing = await fetch_one(db, queries.GET_BY_EMAIL, email)
        if existing:
            return error_result("EMAIL_TAKEN", "Email already registered.")

        await execute(db, queries.UPDATE_EMAIL, email, user_uid)
        await _send_verification_email(user_uid, email)
        logger.info("Added email for %s", user_uid)

    if "password" in data:
        password = data.get("password") or ""
        if weak := weak_password_error(password):
            return weak
        await execute(db, queries.UPDATE_PASSWORD, hash_password(password), user_uid)
        logger.info("Updated password for %s", user_uid)

    if "username" in data:
        username = (data.get("username") or "").strip()
        if not is_valid_username(username):
            return error_result(
                "INVALID_USERNAME",
                "Username must be 3-40 characters (letters, numbers, - or _).",
            )
        existing = await fetch_one(db, queries.GET_BY_USERNAME, username)
        if existing and existing["uid"] != user_uid:
            return error_result("USERNAME_TAKEN", "Username already taken.")
        await execute(db, queries.UPDATE_USERNAME, username, user_uid)
        logger.info("Updated username for %s: %s", user_uid, username)

    if "preferredPlatform" in data:
        platform = data.get("preferredPlatform")
        if platform is not None and platform not in PLATFORMS:
            return error_result("UNKNOWN_PLATFORM", "Unknown platform.")
        await execute(db, queries.UPDATE_PREFERRED_PLATFORM, platform, user_uid)
        logger.info("Updated preferred platform for %s: %s", user_uid, platform)

    row = await fetch_one(db, queries.GET_BY_UID, user_uid)
    return {"status": "success", "message": "Profile updated.", "data": public_user(row)}
