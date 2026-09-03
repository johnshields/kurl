"""
Tests for utils.session -- stateless JWT session tokens.
"""

from unittest.mock import patch

from utils.session import create_session_token, verify_session_token


class TestCreateAndVerify:
    def test_round_trip_returns_the_user_uid(self):
        token = create_session_token("USR_ABC123", "test-secret")
        assert verify_session_token(token, "test-secret") == "USR_ABC123"

    def test_wrong_secret_fails(self):
        token = create_session_token("USR_ABC123", "test-secret")
        assert verify_session_token(token, "wrong-secret") is None

    def test_tampered_token_fails(self):
        token = create_session_token("USR_ABC123", "test-secret")
        assert verify_session_token(token + "x", "test-secret") is None

    def test_garbage_token_fails(self):
        assert verify_session_token("not-a-jwt", "test-secret") is None

    def test_expired_token_fails(self):
        # Fix creation time to the epoch -- exp lands 30 days later, in 1970,
        # always in the past relative to real wall-clock time at verify.
        with patch("utils.session.time") as mock_time:
            mock_time.time.return_value = 0.0
            token = create_session_token("USR_ABC123", "test-secret")

        assert verify_session_token(token, "test-secret") is None
