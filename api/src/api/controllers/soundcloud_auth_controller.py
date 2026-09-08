"""
SoundCloud Auth Controller
Sign in with SoundCloud. No email available, so matching is by
soundcloud_user_id only.
"""

from datetime import UTC, datetime, timedelta

from api.controllers.auth_controller import unique_username
from app.config import settings
from clients import soundcloud_oauth_client
from db.db import execute, fetch_one
from db.queries import soundcloud_accounts as soundcloud_queries
from db.queries import users as user_queries
from models.soundcloud_account import public_soundcloud_account, to_db_params
from models.user import to_db_params as to_user_db_params
from utils.logging import get_logger
from utils.oauth_state import create_oauth_state, verify_oauth_state
from utils.session import create_session_token
from utils.token_crypto import encrypt_token
from utils.uid import gen_uid

logger = get_logger()


def is_configured() -> bool:
    return bool(
        settings.SOUNDCLOUD_CLIENT_ID
        and settings.SOUNDCLOUD_CLIENT_SECRET
        and settings.SOUNDCLOUD_REDIRECT_URI
    )


def build_authorize_url(user_uid: str | None) -> str | None:
    if not is_configured():
        return None
    verifier, challenge = soundcloud_oauth_client.generate_pkce_pair()
    state = create_oauth_state(settings.SESSION_SECRET, user_uid, verifier=verifier)
    return soundcloud_oauth_client.build_authorize_url(
        settings.SOUNDCLOUD_CLIENT_ID, settings.SOUNDCLOUD_REDIRECT_URI, state, challenge
    )


async def handle_callback(db, code: str | None, state: str | None, error: str | None) -> str:
    """Returns the URL to redirect the browser to -- errors become a query
    param on the redirect, not an API error response. Success also carries
    a session token so a new anonymous sign-in is picked up by the app."""
    if error or not code or not state:
        logger.warning("SoundCloud callback missing code/state or carrying an error: %s", error)
        return _app_redirect("error")

    valid, linked_user_uid, code_verifier = verify_oauth_state(state, settings.SESSION_SECRET)
    if not valid or not code_verifier:
        logger.warning("SoundCloud callback state failed verification (expired, tampered, or no PKCE verifier)")
        return _app_redirect("error")

    try:
        tokens = await soundcloud_oauth_client.exchange_code(
            settings.SOUNDCLOUD_CLIENT_ID,
            settings.SOUNDCLOUD_CLIENT_SECRET,
            code,
            settings.SOUNDCLOUD_REDIRECT_URI,
            code_verifier,
        )
        profile = await soundcloud_oauth_client.fetch_profile(tokens["access_token"])
    except Exception as e:
        logger.warning("SoundCloud OAuth exchange failed: %s", e)
        return _app_redirect("error")

    soundcloud_user_id = profile.get("id")
    if not soundcloud_user_id:
        logger.warning("SoundCloud profile had no id")
        return _app_redirect("error")
    soundcloud_user_id = str(soundcloud_user_id)

    if linked_user_uid:
        user_uid = linked_user_uid
    else:
        user_uid = await _resolve_user(db, soundcloud_user_id)

    expires_at = (datetime.now(UTC) + timedelta(seconds=tokens.get("expires_in", 3600))).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    await execute(
        db,
        soundcloud_queries.UPSERT,
        *to_db_params(
            user_uid,
            soundcloud_user_id,
            profile.get("username") or profile.get("full_name"),
            await encrypt_token(tokens["access_token"]) or "",
            await encrypt_token(tokens.get("refresh_token")) or "",
            expires_at,
            tokens.get("scope"),
        ),
    )
    logger.info("Linked SoundCloud account %s for %s", soundcloud_user_id, user_uid)

    session_token = None if linked_user_uid else create_session_token(user_uid, settings.SESSION_SECRET)
    return _app_redirect("connected", session_token)


async def _resolve_user(db, soundcloud_user_id: str) -> str:
    """Find an existing kurl account for this SoundCloud identity, or create one."""
    linked = await fetch_one(db, soundcloud_queries.GET_BY_SOUNDCLOUD_USER_ID, soundcloud_user_id)
    if linked:
        return linked["user_uid"]

    uid = gen_uid("USR")
    username = await unique_username(db)
    await execute(db, user_queries.INSERT, *to_user_db_params(uid, None, username, None))
    logger.info("Created account %s (%s) via SoundCloud sign-in", uid, username)
    return uid


def _app_redirect(status: str, token: str | None = None) -> str:
    url = f"{settings.SOUNDCLOUD_APP_REDIRECT_URL}?soundcloud={status}"
    if token:
        url += f"&token={token}"
    return url


async def get_linked_account(db, user_uid: str) -> dict:
    row = await fetch_one(db, soundcloud_queries.GET_BY_USER_UID, user_uid)
    return public_soundcloud_account(row) if row else {"connected": False}


async def disconnect(db, user_uid: str) -> None:
    await execute(db, soundcloud_queries.DELETE_BY_USER_UID, user_uid)
    logger.info("Unlinked SoundCloud account for %s", user_uid)
