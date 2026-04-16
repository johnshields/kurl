"""
OAuth client-credentials helper
Shared between Spotify and Tidal -- both use the same base64 + POST flow.
"""
import base64

import httpx


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
