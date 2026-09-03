"""
Tests for api.middleware.session_auth -- per-user Bearer token verification,
separate from the shared admin API key checked by middleware.auth.
"""

import sys
from types import ModuleType
from unittest.mock import patch


class _StubResponse:
    def __init__(self, body=None, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}


# `workers` only exists inside the Pyodide/Workers runtime. response.py
# imports it for json_error's Response wrapper -- stub it before import.
_stub = ModuleType("workers")
_stub.Response = _StubResponse
sys.modules.setdefault("workers", _stub)

from api.middleware.session_auth import get_session_user_uid, require_session  # noqa: E402
from utils.session import create_session_token  # noqa: E402


def _req(auth_header: str | None = None):
    class _Request:
        headers = {"Authorization": auth_header} if auth_header else {}

    return _Request()


class TestGetSessionUserUid:
    def test_valid_token_returns_the_uid(self):
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_session_token("USR_X", "test-secret")
            assert get_session_user_uid(_req(f"Bearer {token}")) == "USR_X"

    def test_missing_header_returns_none(self):
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            assert get_session_user_uid(_req()) is None

    def test_invalid_token_returns_none(self):
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            assert get_session_user_uid(_req("Bearer not-a-real-token")) is None

    def test_no_session_secret_configured_returns_none(self):
        """Never crash -- treat as anonymous if the secret isn't set up yet."""
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = None
            token = create_session_token("USR_X", "test-secret")
            assert get_session_user_uid(_req(f"Bearer {token}")) is None


class TestRequireSession:
    def test_valid_token_returns_uid_and_no_error(self):
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_session_token("USR_X", "test-secret")
            user_uid, error = require_session(_req(f"Bearer {token}"))
        assert user_uid == "USR_X"
        assert error is None

    def test_missing_token_returns_401(self):
        with patch("api.middleware.session_auth.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            user_uid, error = require_session(_req())
        assert user_uid is None
        assert error is not None
        assert error.status == 401
