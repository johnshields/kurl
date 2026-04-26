"""
OAuth helpers
TokenCache holds a token + expiry with a 60s safety window. Works for both
client-credentials OAuth (Spotify/Tidal/Audiomack) and locally-signed JWTs
(Apple Music) via get_cached/store.
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
