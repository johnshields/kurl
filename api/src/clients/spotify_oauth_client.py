"""
Spotify OAuth Client
User-authorised Spotify access (Sign in with Spotify) -- authorization_code
grant. Separate from clients/platforms/spotify.py, which is the app-only
client_credentials client used for kurl's own catalog search.
"""

from urllib.parse import urlencode

from app.constants import SPOTIFY_API_BASE, SPOTIFY_AUTHORIZE_URL, SPOTIFY_TOKEN_URL
from clients._http import get_client
from clients.platforms._oauth import fetch_authorization_code_token

# Identity only -- no library/playlist scopes requested in phase A.
SCOPES = "user-read-email"


def build_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """Returns {access_token, refresh_token, expires_in, scope, ...}."""
    return await fetch_authorization_code_token(
        get_client("spotify_oauth"),
        SPOTIFY_TOKEN_URL,
        client_id,
        client_secret,
        code,
        redirect_uri,
    )


async def fetch_profile(access_token: str) -> dict:
    """GET /v1/me -- returns the authorised user's Spotify profile."""
    response = await get_client("spotify_oauth").get(
        f"{SPOTIFY_API_BASE}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()
