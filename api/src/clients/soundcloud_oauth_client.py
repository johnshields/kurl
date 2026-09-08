"""
SoundCloud OAuth Client
Authorization_code + PKCE grant for Sign in with SoundCloud. Separate
from the catalog client_credentials client in clients/platforms/soundcloud.py.

Token exchange sends client_id/secret in the body, not Basic auth.
GET /me has no email field.
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

from app.constants import SOUNDCLOUD_API_BASE, SOUNDCLOUD_AUTHORIZE_URL, SOUNDCLOUD_OAUTH_TOKEN_URL
from clients._http import get_client


def generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) for the S256 PKCE method."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(client_id: str, redirect_uri: str, state: str, code_challenge: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{SOUNDCLOUD_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str, code_verifier: str) -> dict:
    """Returns {access_token, refresh_token, expires_in, scope, ...}."""
    response = await get_client("soundcloud_oauth").post(
        SOUNDCLOUD_OAUTH_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "code": code,
        },
        headers={"Accept": "application/json; charset=utf-8"},
    )
    response.raise_for_status()
    return response.json()


async def fetch_profile(access_token: str) -> dict:
    """GET /me -- returns the authorised user's SoundCloud profile."""
    response = await get_client("soundcloud_oauth").get(
        f"{SOUNDCLOUD_API_BASE}/me",
        headers={"Authorization": f"OAuth {access_token}"},
    )
    response.raise_for_status()
    return response.json()
