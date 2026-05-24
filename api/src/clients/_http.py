"""
Shared HTTP client factory.
One cached AsyncClient per name. Kwargs are applied on first creation only
(timeout, headers, follow_redirects, etc).
"""

import httpx

from app.constants import CLIENT_TIMEOUT

_clients: dict[str, httpx.AsyncClient] = {}


def get_client(name: str, **kwargs) -> httpx.AsyncClient:
    if name not in _clients:
        kwargs.setdefault("timeout", CLIENT_TIMEOUT)
        _clients[name] = httpx.AsyncClient(**kwargs)
    return _clients[name]
