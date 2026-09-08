"""
Google Auth Controller
Sign in with YouTube: identity only, anonymous or linked to an existing session.
"""

from datetime import UTC, datetime, timedelta

from api.controllers.auth_controller import unique_username
from app.config import settings
from clients import google_oauth_client
from db.db import execute, fetch_one
from db.queries import google_accounts as google_queries
from db.queries import users as user_queries
from models.google_account import public_google_account, to_db_params
from models.user import to_db_params as to_user_db_params
from utils.logging import get_logger
from utils.oauth_state import create_oauth_state, verify_oauth_state
from utils.session import create_session_token
from utils.uid import gen_uid

logger = get_logger()


def is_configured() -> bool:
    return bool(
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and settings.GOOGLE_REDIRECT_URI
    )


def build_authorize_url(user_uid: str | None) -> str | None:
    if not is_configured():
        return None
    state = create_oauth_state(settings.SESSION_SECRET, user_uid)
    return google_oauth_client.build_authorize_url(
        settings.GOOGLE_CLIENT_ID, settings.GOOGLE_REDIRECT_URI, state
    )


async def handle_callback(db, code: str | None, state: str | None, error: str | None) -> str:
    """Returns the URL to redirect the browser to -- errors become a query
    param on the redirect, not an API error response. Success also carries
    a session token so a new anonymous sign-in is picked up by the app."""
    if error or not code or not state:
        logger.warning("Google callback missing code/state or carrying an error: %s", error)
        return _app_redirect("error")

    valid, linked_user_uid, _ = verify_oauth_state(state, settings.SESSION_SECRET)
    if not valid:
        logger.warning("Google callback state failed verification (expired or tampered)")
        return _app_redirect("error")

    try:
        tokens = await google_oauth_client.exchange_code(
            settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, code, settings.GOOGLE_REDIRECT_URI
        )
        profile = await google_oauth_client.fetch_profile(tokens["access_token"])
    except Exception as e:
        logger.warning("Google OAuth exchange failed: %s", e)
        return _app_redirect("error")

    google_user_id = profile.get("sub")
    if not google_user_id:
        logger.warning("Google profile had no sub")
        return _app_redirect("error")

    if linked_user_uid:
        user_uid = linked_user_uid
    else:
        user_uid = await _resolve_user(db, google_user_id, profile.get("email"))

    expires_at = (datetime.now(UTC) + timedelta(seconds=tokens.get("expires_in", 3600))).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    await execute(
        db,
        google_queries.UPSERT,
        *to_db_params(
            user_uid,
            google_user_id,
            profile.get("name"),
            tokens["access_token"],
            tokens.get("refresh_token", ""),
            expires_at,
            tokens.get("scope"),
        ),
    )
    logger.info("Linked Google account %s for %s", google_user_id, user_uid)

    session_token = None if linked_user_uid else create_session_token(user_uid, settings.SESSION_SECRET)
    return _app_redirect("connected", session_token)


async def _resolve_user(db, google_user_id: str, email: str | None) -> str:
    """Find an existing kurl account for this Google identity, or create one."""
    linked = await fetch_one(db, google_queries.GET_BY_GOOGLE_USER_ID, google_user_id)
    if linked:
        return linked["user_uid"]

    async def _by_email():
        return await fetch_one(db, user_queries.GET_BY_EMAIL, email) if email else None

    if existing := await _by_email():
        return existing["uid"]

    uid = gen_uid("USR")
    username = await unique_username(db)
    try:
        await execute(db, user_queries.INSERT, *to_user_db_params(uid, email, username, None))
    except Exception as e:
        if existing := await _by_email():
            return existing["uid"]
        logger.warning("Failed to create account for Google sign-in: %s", e)
        raise
    logger.info("Created account %s (%s) via Google sign-in", uid, username)
    return uid


def _app_redirect(status: str, token: str | None = None) -> str:
    url = f"{settings.GOOGLE_APP_REDIRECT_URL}?google={status}"
    if token:
        url += f"&token={token}"
    return url


async def get_linked_account(db, user_uid: str) -> dict:
    row = await fetch_one(db, google_queries.GET_BY_USER_UID, user_uid)
    return public_google_account(row) if row else {"connected": False}


async def disconnect(db, user_uid: str) -> None:
    await execute(db, google_queries.DELETE_BY_USER_UID, user_uid)
    logger.info("Unlinked Google account for %s", user_uid)
