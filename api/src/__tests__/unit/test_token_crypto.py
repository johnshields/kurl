"""
Tests for utils.token_crypto -- only the pure-Python guard paths. The
actual crypto.subtle round trip needs a real Pyodide/Workers runtime and
can't run under pytest.
"""

from unittest.mock import patch

from utils import token_crypto


class TestIsConfigured:
    def test_false_when_no_key(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = None
            assert token_crypto.is_configured() is False

    def test_true_when_key_present(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = "a" * 64
            assert token_crypto.is_configured() is True


class TestEncryptToken:
    async def test_returns_none_for_empty_input(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = "a" * 64
            assert await token_crypto.encrypt_token(None) is None
            assert await token_crypto.encrypt_token("") is None

    async def test_returns_none_when_not_configured(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = None
            assert await token_crypto.encrypt_token("a-real-token") is None


class TestDecryptToken:
    async def test_returns_none_for_empty_input(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = "a" * 64
            assert await token_crypto.decrypt_token(None) is None
            assert await token_crypto.decrypt_token("") is None

    async def test_returns_none_when_not_configured(self):
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = None
            assert await token_crypto.decrypt_token("iv:ciphertext") is None

    async def test_returns_none_for_malformed_input(self):
        """No ':' separator -- fails closed instead of raising."""
        with patch("utils.token_crypto.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = "a" * 64
            assert await token_crypto.decrypt_token("not-valid") is None
