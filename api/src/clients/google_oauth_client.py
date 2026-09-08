"""
Google OAuth Client
Authorization_code grant for Sign in with YouTube. Separate from
settings.YOUTUBE_API_KEY, an unrelated Data API v3 key.

Token exchange sends client_id/secret in the body, not Basic auth.
"""

from urllib.parse import urlencode

from app.constants import GOOGLE_AUTHORIZE_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL
from clients._http import get_client

# Identity only -- no YouTube data scopes requested.
SCOPES = "openid email profile"


def build_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "access_type": "offline",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """Returns {access_token, refresh_token?, expires_in, scope, ...}."""
    response = await get_client("google_oauth").post(
        GOOGLE_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )
    response.raise_for_status()
    return response.json()


async def fetch_profile(access_token: str) -> dict:
    """GET /userinfo -- returns the authorised user's Google profile."""
    response = await get_client("google_oauth").get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()
