"""
OAuth Sign-in Engine
Shared authorization_code flow for the streaming-platform sign-ins.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from api.controllers.auth_controller import unique_username
from app.config import settings
from db.db import execute, fetch_one
from db.queries import users as user_queries
from models.user import to_db_params as to_user_db_params
from utils.logging import get_logger
from utils.oauth_state import create_oauth_state, verify_oauth_state
from utils.session import create_session_token
from utils.token_crypto import encrypt_token
from utils.uid import gen_uid

logger = get_logger()


@dataclass(frozen=True)
class OAuthProvider:
    key: str
    label: str
    settings_prefix: str
    client: Any
    queries: Any
    to_db_params: Callable
    public_account: Callable
    get_by_provider_id_query: str
    profile_id_key: str
    display_name_keys: tuple[str, ...]
    uses_pkce: bool = False
    has_email: bool = True

    def _setting(self, suffix: str):
        return getattr(settings, f"{self.settings_prefix}_{suffix}")


def is_configured(p: OAuthProvider) -> bool:
    return bool(
        p._setting("CLIENT_ID")
        and p._setting("CLIENT_SECRET")
        and p._setting("REDIRECT_URI")
    )


def build_authorize_url(p: OAuthProvider, user_uid: str | None) -> str | None:
    if not is_configured(p):
        return None
    client_id = p._setting("CLIENT_ID")
    redirect_uri = p._setting("REDIRECT_URI")
    if p.uses_pkce:
        verifier, challenge = p.client.generate_pkce_pair()
        state = create_oauth_state(settings.SESSION_SECRET, user_uid, verifier=verifier)
        return p.client.build_authorize_url(client_id, redirect_uri, state, challenge)
    state = create_oauth_state(settings.SESSION_SECRET, user_uid)
    return p.client.build_authorize_url(client_id, redirect_uri, state)


async def handle_callback(
    p: OAuthProvider, db, code: str | None, state: str | None, error: str | None
) -> str:
    """Returns the URL to redirect the browser to -- errors become a query
    param on the redirect, not an API error response. Success also carries
    a session token so a new anonymous sign-in is picked up by the app."""
    if error or not code or not state:
        logger.warning("%s callback missing code/state or carrying an error: %s", p.label, error)
        return _app_redirect(p, "error")

    valid, linked_user_uid, code_verifier = verify_oauth_state(state, settings.SESSION_SECRET)
    if not valid or (p.uses_pkce and not code_verifier):
        logger.warning("%s callback state failed verification (expired, tampered, or no PKCE verifier)", p.label)
        return _app_redirect(p, "error")

    try:
        if p.uses_pkce:
            tokens = await p.client.exchange_code(
                p._setting("CLIENT_ID"),
                p._setting("CLIENT_SECRET"),
                code,
                p._setting("REDIRECT_URI"),
                code_verifier,
            )
        else:
            tokens = await p.client.exchange_code(
                p._setting("CLIENT_ID"), p._setting("CLIENT_SECRET"), code, p._setting("REDIRECT_URI")
            )
        profile = await p.client.fetch_profile(tokens["access_token"])
    except Exception as e:
        logger.warning("%s OAuth exchange failed: %s", p.label, e)
        return _app_redirect(p, "error")

    provider_user_id = profile.get(p.profile_id_key)
    if not provider_user_id:
        logger.warning("%s profile had no %s", p.label, p.profile_id_key)
        return _app_redirect(p, "error")
    provider_user_id = str(provider_user_id)

    if linked_user_uid:
        user_uid = linked_user_uid
    else:
        user_uid = await _resolve_user(p, db, provider_user_id, profile.get("email"))

    expires_at = (datetime.now(UTC) + timedelta(seconds=tokens.get("expires_in", 3600))).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    display_name = next((profile.get(k) for k in p.display_name_keys if profile.get(k)), None)

    await execute(
        db,
        p.queries.UPSERT,
        *p.to_db_params(
            user_uid,
            provider_user_id,
            display_name,
            await encrypt_token(tokens["access_token"]) or "",
            await encrypt_token(tokens.get("refresh_token")) or "",
            expires_at,
            tokens.get("scope"),
        ),
    )
    logger.info("Linked %s account %s for %s", p.label, provider_user_id, user_uid)

    session_token = None if linked_user_uid else create_session_token(user_uid, settings.SESSION_SECRET)
    return _app_redirect(p, "connected", session_token)


async def _resolve_user(p: OAuthProvider, db, provider_user_id: str, email: str | None) -> str:
    """Find an existing kurl account for this provider identity, or create one."""
    linked = await fetch_one(db, p.get_by_provider_id_query, provider_user_id)
    if linked:
        return linked["user_uid"]

    async def _by_email():
        return await fetch_one(db, user_queries.GET_BY_EMAIL, email) if (p.has_email and email) else None

    if existing := await _by_email():
        return existing["uid"]

    uid = gen_uid("USR")
    username = await unique_username(db)
    try:
        await execute(db, user_queries.INSERT, *to_user_db_params(uid, email if p.has_email else None, username, None))
    except Exception as e:
        # Rare race: another request just took this email -- use that account.
        if existing := await _by_email():
            return existing["uid"]
        logger.warning("Failed to create account for %s sign-in: %s", p.label, e)
        raise
    logger.info("Created account %s (%s) via %s sign-in", uid, username, p.label)
    return uid


def _app_redirect(p: OAuthProvider, status: str, token: str | None = None) -> str:
    url = f"{p._setting('APP_REDIRECT_URL')}?{p.key}={status}"
    if token:
        url += f"&token={token}"
    return url


async def get_linked_account(p: OAuthProvider, db, user_uid: str) -> dict:
    row = await fetch_one(db, p.queries.GET_BY_USER_UID, user_uid)
    return p.public_account(row) if row else {"connected": False}


async def disconnect(p: OAuthProvider, db, user_uid: str) -> None:
    await execute(db, p.queries.DELETE_BY_USER_UID, user_uid)
    logger.info("Unlinked %s account for %s", p.label, user_uid)
