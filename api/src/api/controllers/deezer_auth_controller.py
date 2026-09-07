"""
Deezer Auth Controller
Sign in with Deezer -- one flow, two modes: anonymous (find/create an
account) or linked (tie Deezer to an already-signed-in session). Identity
only -- no library/playlist scopes requested.
"""

from datetime import UTC, datetime, timedelta

from api.controllers.auth_controller import unique_username
from app.config import settings
from clients import deezer_oauth_client
from db.db import execute, fetch_one
from db.queries import deezer_accounts as deezer_queries
from db.queries import users as user_queries
from models.deezer_account import public_deezer_account, to_db_params
from models.user import to_db_params as to_user_db_params
from utils.logging import get_logger
from utils.oauth_state import create_oauth_state, verify_oauth_state
from utils.session import create_session_token
from utils.uid import gen_uid

logger = get_logger()


def is_configured() -> bool:
    return bool(
        settings.DEEZER_APP_ID
        and settings.DEEZER_APP_SECRET
        and settings.DEEZER_REDIRECT_URI
    )


def build_authorize_url(user_uid: str | None) -> str | None:
    if not is_configured():
        return None
    state = create_oauth_state(settings.SESSION_SECRET, user_uid)
    # State travels inside redirect_uri itself -- see deezer_oauth_client.
    redirect_uri = f"{settings.DEEZER_REDIRECT_URI}?state={state}"
    return deezer_oauth_client.build_authorize_url(settings.DEEZER_APP_ID, redirect_uri)


async def handle_callback(db, code: str | None, state: str | None, error: str | None) -> str:
    """Returns the URL to redirect the browser to -- errors become a query
    param on the redirect, not an API error response. Success also carries
    a session token so a new anonymous sign-in is picked up by the app."""
    if error or not code or not state:
        logger.warning("Deezer callback missing code/state or carrying an error: %s", error)
        return _app_redirect("error")

    valid, linked_user_uid, _ = verify_oauth_state(state, settings.SESSION_SECRET)
    if not valid:
        logger.warning("Deezer callback state failed verification (expired or tampered)")
        return _app_redirect("error")

    try:
        tokens = await deezer_oauth_client.exchange_code(
            settings.DEEZER_APP_ID, settings.DEEZER_APP_SECRET, code
        )
        if "access_token" not in tokens:
            raise ValueError(f"Deezer token exchange returned no access_token: {tokens}")
        profile = await deezer_oauth_client.fetch_profile(tokens["access_token"])
    except Exception as e:
        logger.warning("Deezer OAuth exchange failed: %s", e)
        return _app_redirect("error")

    deezer_user_id = profile.get("id")
    if not deezer_user_id:
        logger.warning("Deezer profile had no id")
        return _app_redirect("error")
    deezer_user_id = str(deezer_user_id)

    if linked_user_uid:
        user_uid = linked_user_uid
    else:
        user_uid = await _resolve_user(db, deezer_user_id, profile.get("email"))

    expires_in = int(tokens.get("expires") or 0)
    expires_at = (
        (datetime.now(UTC) + timedelta(seconds=expires_in)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if expires_in > 0
        else None
    )

    await execute(
        db,
        deezer_queries.UPSERT,
        *to_db_params(
            user_uid,
            deezer_user_id,
            profile.get("name"),
            tokens["access_token"],
            expires_at,
        ),
    )
    logger.info("Linked Deezer account %s for %s", deezer_user_id, user_uid)

    session_token = None if linked_user_uid else create_session_token(user_uid, settings.SESSION_SECRET)
    return _app_redirect("connected", session_token)


async def _resolve_user(db, deezer_user_id: str, email: str | None) -> str:
    """Find an existing kurl account for this Deezer identity, or create one."""
    linked = await fetch_one(db, deezer_queries.GET_BY_DEEZER_USER_ID, deezer_user_id)
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
        # Rare race: another request just took this email -- use that account.
        if existing := await _by_email():
            return existing["uid"]
        logger.warning("Failed to create account for Deezer sign-in: %s", e)
        raise
    logger.info("Created account %s (%s) via Deezer sign-in", uid, username)
    return uid


def _app_redirect(status: str, token: str | None = None) -> str:
    url = f"{settings.DEEZER_APP_REDIRECT_URL}?deezer={status}"
    if token:
        url += f"&token={token}"
    return url


async def get_linked_account(db, user_uid: str) -> dict:
    row = await fetch_one(db, deezer_queries.GET_BY_USER_UID, user_uid)
    return public_deezer_account(row) if row else {"connected": False}


async def disconnect(db, user_uid: str) -> None:
    await execute(db, deezer_queries.DELETE_BY_USER_UID, user_uid)
    logger.info("Unlinked Deezer account for %s", user_uid)
