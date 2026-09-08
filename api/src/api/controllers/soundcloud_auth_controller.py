"""
SoundCloud Auth Controller
Sign in with SoundCloud. No email available, so matching is by
soundcloud_user_id only.
"""

from functools import partial

from api.controllers import oauth_signin
from clients import soundcloud_oauth_client
from db.queries.streaming_accounts import account_queries
from models.streaming_account import public_account, to_db_params

PROVIDER = oauth_signin.OAuthProvider(
    key="soundcloud",
    label="SoundCloud",
    settings_prefix="SOUNDCLOUD",
    client=soundcloud_oauth_client,
    queries=account_queries("soundcloud_accounts", "soundcloud_user_id"),
    to_db_params=to_db_params,
    public_account=partial(public_account, id_column="soundcloud_user_id", id_key="soundcloudUserId"),
    profile_id_key="id",
    display_name_keys=("username", "full_name"),
    uses_pkce=True,
    has_email=False,
)


def is_configured() -> bool:
    return oauth_signin.is_configured(PROVIDER)


def build_authorize_url(user_uid: str | None) -> str | None:
    return oauth_signin.build_authorize_url(PROVIDER, user_uid)


async def handle_callback(db, code: str | None, state: str | None, error: str | None) -> str:
    return await oauth_signin.handle_callback(PROVIDER, db, code, state, error)


async def get_linked_account(db, user_uid: str) -> dict:
    return await oauth_signin.get_linked_account(PROVIDER, db, user_uid)


async def disconnect(db, user_uid: str) -> None:
    await oauth_signin.disconnect(PROVIDER, db, user_uid)
