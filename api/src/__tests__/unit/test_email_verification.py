"""
Tests for utils.email_verification -- signed email-verification tokens.
"""

from unittest.mock import patch

from utils.email_verification import create_verification_token, decode_verification_token


class TestCreateAndDecode:
    def test_round_trip_returns_the_user_uid(self):
        token = create_verification_token("USR_ABC123", "test-secret")
        assert decode_verification_token(token, "test-secret") == "USR_ABC123"

    def test_wrong_secret_fails(self):
        token = create_verification_token("USR_ABC123", "test-secret")
        assert decode_verification_token(token, "wrong-secret") is None

    def test_tampered_token_fails(self):
        token = create_verification_token("USR_ABC123", "test-secret")
        assert decode_verification_token(token + "x", "test-secret") is None

    def test_garbage_token_fails(self):
        assert decode_verification_token("not-a-jwt", "test-secret") is None

    def test_expired_token_fails(self):
        with patch("utils.email_verification.time") as mock_time:
            mock_time.time.return_value = 0.0
            token = create_verification_token("USR_ABC123", "test-secret")

        assert decode_verification_token(token, "test-secret") is None
