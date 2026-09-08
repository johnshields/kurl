"""
Spotify Auth Controller
Sign in with Spotify: identity only, anonymous or linked to an existing session.
"""

from api.controllers import oauth_signin
from clients import spotify_oauth_client
from db.queries import spotify_accounts as spotify_queries
from models.spotify_account import public_spotify_account, to_db_params

PROVIDER = oauth_signin.OAuthProvider(
    key="spotify",
    label="Spotify",
    settings_prefix="SPOTIFY",
    client=spotify_oauth_client,
    queries=spotify_queries,
    to_db_params=to_db_params,
    public_account=public_spotify_account,
    get_by_provider_id_query=spotify_queries.GET_BY_SPOTIFY_USER_ID,
    profile_id_key="id",
    display_name_keys=("display_name",),
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
