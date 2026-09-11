"""
Tests for utils.message_crypto -- the not-configured guard and the
plaintext/ciphertext heuristic. crypto.subtle only runs under Pyodide.
"""

from unittest.mock import patch

import pytest

from utils.message_crypto import MessageCryptoError, _looks_encrypted, decrypt_body, encrypt_body


class TestNotConfigured:
    async def test_encrypt_raises_without_a_key(self):
        with patch("utils.message_crypto.settings") as mock_settings:
            mock_settings.MESSAGE_ENCRYPTION_KEY = None
            with pytest.raises(MessageCryptoError):
                await encrypt_body("hello")

    async def test_decrypt_raises_for_ciphertext_shaped_input_without_a_key(self):
        with patch("utils.message_crypto.settings") as mock_settings:
            mock_settings.MESSAGE_ENCRYPTION_KEY = None
            with pytest.raises(MessageCryptoError):
                await decrypt_body("aGVsbG8=:d29ybGQ=")


class TestDecryptPassthrough:
    async def test_plain_text_with_no_colon_is_returned_unchanged(self):
        assert await decrypt_body("just a normal message") == "just a normal message"

    async def test_plain_text_containing_a_colon_is_returned_unchanged(self):
        assert await decrypt_body("check this: it's great") == "check this: it's great"

    async def test_none_and_empty_pass_through(self):
        assert await decrypt_body(None) is None
        assert await decrypt_body("") == ""


class TestLooksEncrypted:
    def test_true_for_iv_ciphertext_shape(self):
        assert _looks_encrypted("aGVsbG8=:d29ybGQ=")

    def test_false_without_a_colon(self):
        assert not _looks_encrypted("hello world")

    def test_false_when_a_half_is_not_valid_base64(self):
        assert not _looks_encrypted("not base64 at all:d29ybGQ=")

    def test_false_for_an_empty_half(self):
        assert not _looks_encrypted(":d29ybGQ=")
        assert not _looks_encrypted("aGVsbG8=:")
