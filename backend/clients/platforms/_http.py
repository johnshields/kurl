"""
Shared HTTP client factory
One cached AsyncClient per platform name. Kwargs are applied on first creation
only (e.g. follow_redirects for SoundCloud).
"""

import httpx

from app.constants import CLIENT_TIMEOUT

_clients: dict[str, httpx.AsyncClient] = {}


def get_client(name: str, **kwargs) -> httpx.AsyncClient:
    if name not in _clients:
        _clients[name] = httpx.AsyncClient(timeout=CLIENT_TIMEOUT, **kwargs)
    return _clients[name]
