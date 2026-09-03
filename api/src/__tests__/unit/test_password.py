"""
Tests for utils.password -- PBKDF2-HMAC-SHA256 hashing, stdlib only.
"""

from utils.password import hash_password, verify_password


class TestHashPassword:
    def test_hash_is_not_the_plain_password(self):
        assert hash_password("correct horse battery staple") != "correct horse battery staple"

    def test_same_password_hashes_differently_each_time(self):
        """Salt must differ per call, even for the same input."""
        assert hash_password("hunter2") != hash_password("hunter2")

    def test_hash_contains_a_salt_separator(self):
        assert "$" in hash_password("hunter2")


class TestVerifyPassword:
    def test_correct_password_verifies(self):
        stored = hash_password("hunter2")
        assert verify_password("hunter2", stored) is True

    def test_wrong_password_fails(self):
        stored = hash_password("hunter2")
        assert verify_password("wrong-password", stored) is False

    def test_malformed_stored_value_fails_safely(self):
        assert verify_password("hunter2", "not-a-valid-hash") is False

    def test_empty_stored_value_fails_safely(self):
        assert verify_password("hunter2", "") is False
