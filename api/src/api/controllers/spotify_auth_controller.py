"""
Spotify Auth Controller
Sign in with Spotify. Two modes through the same authorize/callback flow:

- Anonymous (no session at /start) -- full sign-in. The callback finds an
  existing kurl account for this Spotify identity (by prior link, then by
  matching email), or creates a brand-new one, then issues a session token.
- Linked (a valid session at /start) -- "Connect Spotify" from Settings,
  ties Spotify to that already-signed-in account instead.

Phase A scope: identity only, no library/playlist scopes.
"""

from datetime import UTC, datetime, timedelta

from app.config import settings
from clients import spotify_oauth_client
from db.db import execute, fetch_one
from db.queries import spotify_accounts as spotify_queries
from db.queries import users as user_queries
from models.spotify_account import public_spotify_account, to_db_params
from models.user import to_db_params as to_user_db_params
from utils.logging import get_logger
from utils.oauth_state import create_oauth_state, verify_oauth_state
from utils.session import create_session_token
from utils.uid import gen_uid

logger = get_logger()


def is_configured() -> bool:
    return bool(
        settings.SPOTIFY_CLIENT_ID
        and settings.SPOTIFY_CLIENT_SECRET
        and settings.SPOTIFY_REDIRECT_URI
    )


def build_authorize_url(user_uid: str | None) -> str | None:
    if not is_configured():
        return None
    state = create_oauth_state(settings.SESSION_SECRET, user_uid)
    return spotify_oauth_client.build_authorize_url(
        settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_REDIRECT_URI, state
    )


async def handle_callback(db, code: str | None, state: str | None, error: str | None) -> str:
    """Exchanges the code, links/creates the account, and returns the URL to
    send the browser to -- this is a browser redirect, so errors never
    become an API error response, only a different query param on the same
    redirect. On success the redirect also carries a session token so a
    brand-new (anonymous sign-in) session is picked up by the app."""
    if error or not code or not state:
        logger.warning("Spotify callback missing code/state or carrying an error: %s", error)
        return _app_redirect("error")

    valid, linked_user_uid = verify_oauth_state(state, settings.SESSION_SECRET)
    if not valid:
        logger.warning("Spotify callback state failed verification (expired or tampered)")
        return _app_redirect("error")

    try:
        tokens = await spotify_oauth_client.exchange_code(
            settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET, code, settings.SPOTIFY_REDIRECT_URI
        )
        profile = await spotify_oauth_client.fetch_profile(tokens["access_token"])
    except Exception as e:
        logger.warning("Spotify OAuth exchange failed: %s", e)
        return _app_redirect("error")

    spotify_user_id = profile.get("id")
    if not spotify_user_id:
        logger.warning("Spotify profile had no id")
        return _app_redirect("error")

    if linked_user_uid:
        # Explicit link from an already-authenticated session.
        user_uid = linked_user_uid
    else:
        # Anonymous sign-in -- find or create the account for this identity.
        user_uid = await _resolve_user(db, spotify_user_id, profile.get("email"))

    expires_at = (datetime.now(UTC) + timedelta(seconds=tokens.get("expires_in", 3600))).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    await execute(
        db,
        spotify_queries.UPSERT,
        *to_db_params(
            user_uid,
            spotify_user_id,
            profile.get("display_name"),
            tokens["access_token"],
            tokens.get("refresh_token", ""),
            expires_at,
            tokens.get("scope"),
        ),
    )
    logger.info("Linked Spotify account %s for %s", spotify_user_id, user_uid)

    session_token = create_session_token(user_uid, settings.SESSION_SECRET)
    return _app_redirect("connected", session_token)


async def _resolve_user(db, spotify_user_id: str, email: str | None) -> str:
    """Find an existing kurl account for this Spotify identity, or create one."""
    linked = await fetch_one(db, spotify_queries.GET_BY_SPOTIFY_USER_ID, spotify_user_id)
    if linked:
        return linked["user_uid"]

    if email:
        existing = await fetch_one(db, user_queries.GET_BY_EMAIL, email)
        if existing:
            return existing["uid"]

    # Deferred import -- avoids a hard dependency cycle between the two
    # controllers; auth_controller doesn't otherwise need to know about Spotify.
    from api.controllers.auth_controller import unique_username

    uid = gen_uid("USR")
    username = await unique_username(db)
    try:
        await execute(db, user_queries.INSERT, *to_user_db_params(uid, email, username, None))
    except Exception as e:
        # Rare race: another request just took this email -- use that account.
        if email:
            existing = await fetch_one(db, user_queries.GET_BY_EMAIL, email)
            if existing:
                return existing["uid"]
        logger.warning("Failed to create account for Spotify sign-in: %s", e)
        raise
    logger.info("Created account %s (%s) via Spotify sign-in", uid, username)
    return uid


def _app_redirect(status: str, token: str | None = None) -> str:
    url = f"{settings.SPOTIFY_APP_REDIRECT_URL}?spotify={status}"
    if token:
        url += f"&token={token}"
    return url


async def get_linked_account(db, user_uid: str) -> dict:
    row = await fetch_one(db, spotify_queries.GET_BY_USER_UID, user_uid)
    return public_spotify_account(row) if row else {"connected": False}


async def disconnect(db, user_uid: str) -> None:
    await execute(db, spotify_queries.DELETE_BY_USER_UID, user_uid)
    logger.info("Unlinked Spotify account for %s", user_uid)
