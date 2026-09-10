"""
Tests for utils.auth.oauth_state -- short-lived signed OAuth state tokens.
"""

from unittest.mock import patch

from utils.auth.oauth_state import create_oauth_state, verify_oauth_state


class TestAnonymousState:
    def test_round_trip_has_no_subject(self):
        state = create_oauth_state("test-secret")
        assert verify_oauth_state(state, "test-secret") == (True, None, None)

    def test_wrong_secret_fails(self):
        state = create_oauth_state("test-secret")
        assert verify_oauth_state(state, "wrong-secret") == (False, None, None)

    def test_tampered_token_fails(self):
        state = create_oauth_state("test-secret")
        assert verify_oauth_state(state + "x", "test-secret") == (False, None, None)

    def test_garbage_token_fails(self):
        assert verify_oauth_state("not-a-jwt", "test-secret") == (False, None, None)

    def test_expired_token_fails(self):
        with patch("utils.auth.jwt_token.time") as mock_time:
            mock_time.time.return_value = 0.0
            state = create_oauth_state("test-secret")

        assert verify_oauth_state(state, "test-secret") == (False, None, None)


class TestLinkedState:
    def test_round_trip_returns_the_user_uid(self):
        state = create_oauth_state("test-secret", user_uid="USR_ABC123")
        assert verify_oauth_state(state, "test-secret") == (True, "USR_ABC123", None)

    def test_wrong_secret_fails(self):
        state = create_oauth_state("test-secret", user_uid="USR_ABC123")
        assert verify_oauth_state(state, "wrong-secret") == (False, None, None)


class TestPkceVerifier:
    def test_round_trip_returns_the_verifier(self):
        state = create_oauth_state("test-secret", verifier="verifier-abc")
        assert verify_oauth_state(state, "test-secret") == (True, None, "verifier-abc")

    def test_round_trip_returns_both_subject_and_verifier(self):
        state = create_oauth_state("test-secret", user_uid="USR_ABC123", verifier="verifier-abc")
        assert verify_oauth_state(state, "test-secret") == (True, "USR_ABC123", "verifier-abc")
