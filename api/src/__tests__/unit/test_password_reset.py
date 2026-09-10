"""
Tests for utils.auth.password_reset -- stateless forgot-password tokens.
"""

from unittest.mock import patch

from utils.auth.password_reset import create_reset_token, decode_reset_token, matches_current_password


class TestCreateAndDecode:
    def test_round_trip_returns_uid_and_fingerprint(self):
        token = create_reset_token("USR_X", "some-hash", "test-secret")
        decoded = decode_reset_token(token, "test-secret")
        assert decoded is not None
        uid, fingerprint = decoded
        assert uid == "USR_X"
        assert matches_current_password(fingerprint, "some-hash")

    def test_wrong_secret_fails(self):
        token = create_reset_token("USR_X", "some-hash", "test-secret")
        assert decode_reset_token(token, "wrong-secret") is None

    def test_tampered_token_fails(self):
        token = create_reset_token("USR_X", "some-hash", "test-secret")
        assert decode_reset_token(token + "x", "test-secret") is None

    def test_garbage_token_fails(self):
        assert decode_reset_token("not-a-jwt", "test-secret") is None

    def test_expired_token_fails(self):
        with patch("utils.auth.jwt_token.time") as mock_time:
            mock_time.time.return_value = 0.0
            token = create_reset_token("USR_X", "some-hash", "test-secret")
        assert decode_reset_token(token, "test-secret") is None


class TestMatchesCurrentPassword:
    def test_fails_once_password_hash_changes(self):
        """The whole point -- reusing a stale token after the password
        already changed must fail, with no separate used-token table."""
        token = create_reset_token("USR_X", "old-hash", "test-secret")
        _, fingerprint = decode_reset_token(token, "test-secret")
        assert matches_current_password(fingerprint, "old-hash") is True
        assert matches_current_password(fingerprint, "new-hash") is False

    def test_handles_no_password_set_yet(self):
        """Spotify-only accounts have no password_hash -- still round-trips."""
        token = create_reset_token("USR_X", None, "test-secret")
        _, fingerprint = decode_reset_token(token, "test-secret")
        assert matches_current_password(fingerprint, None) is True
