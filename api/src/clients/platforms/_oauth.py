"""
OAuth helpers
TokenCache holds a token + expiry with a 60s safety window. Works for both
client-credentials OAuth (Spotify, Tidal) and locally-signed JWTs
(Apple Music) via get_cached/store.

fetch_authorization_code_token/refresh_authorization_token are a separate
grant type -- user-authorised (Sign in with Spotify), not app-only. They
don't use TokenCache: those tokens are per-user and persisted in D1, not
cached in-process.
"""

import base64
import time

import httpx

from utils.logging import get_logger

logger = get_logger()


class TokenCache:
    def __init__(self, label: str):
        self._label = label
        self._token: str | None = None
        self._expires_at: float = 0

    def get_cached(self) -> str | None:
        """Return the cached token if still valid, else None."""
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        return None

    def store(self, token: str, expires_in: int) -> str:
        self._token = token
        self._expires_at = time.time() + expires_in
        logger.info("%s token refreshed, expires in %ss", self._label, expires_in)
        return token

    async def fetch_via_oauth(
        self,
        http_client: httpx.AsyncClient,
        token_url: str,
        client_id: str,
        client_secret: str,
    ) -> str:
        """Get a valid token, refreshing via client_credentials grant when stale."""
        if cached := self.get_cached():
            return cached
        token, expires_in = await fetch_client_credentials_token(
            http_client,
            token_url,
            client_id,
            client_secret,
        )
        return self.store(token, expires_in)


async def fetch_client_credentials_token(
    http_client: httpx.AsyncClient,
    token_url: str,
    client_id: str,
    client_secret: str,
) -> tuple[str, int]:
    """Fetch an OAuth token via client_credentials grant. Returns (token, expires_in)."""
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = await http_client.post(
        token_url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"], data.get("expires_in", 3600)


async def fetch_authorization_code_token(
    http_client: httpx.AsyncClient,
    token_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict:
    """Exchange a user-authorised code for tokens (authorization_code grant).

    Returns the raw {access_token, refresh_token, expires_in, scope, ...}
    payload -- unlike fetch_client_credentials_token, callers need more than
    just the access token here.
    """
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = await http_client.post(
        token_url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
    )
    response.raise_for_status()
    return response.json()


async def refresh_authorization_token(
    http_client: httpx.AsyncClient,
    token_url: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict:
    """Exchange a refresh token for a new access token (refresh_token grant).

    Spotify may or may not return a new refresh_token in the response --
    callers should keep the old one when it's absent.
    """
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = await http_client.post(
        token_url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
    )
    response.raise_for_status()
    return response.json()
