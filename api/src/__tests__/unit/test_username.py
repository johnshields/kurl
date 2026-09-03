"""
Tests for utils.username -- coolname-based generation and validation.
"""

from utils.username import generate_username, generate_username_with_suffix, is_valid_username


class TestGenerateUsername:
    def test_generates_a_valid_username(self):
        assert is_valid_username(generate_username())

    def test_two_calls_are_very_likely_different(self):
        # coolname's word pool is large enough that a collision here would
        # indicate something is broken, not bad luck.
        names = {generate_username() for _ in range(20)}
        assert len(names) > 1


class TestGenerateUsernameWithSuffix:
    def test_generates_a_valid_username(self):
        assert is_valid_username(generate_username_with_suffix())

    def test_includes_a_hex_suffix(self):
        name = generate_username_with_suffix()
        suffix = name.rsplit("-", 1)[-1]
        assert len(suffix) == 4
        int(suffix, 16)  # raises ValueError if not valid hex


class TestIsValidUsername:
    def test_accepts_letters_numbers_hyphen_underscore(self):
        assert is_valid_username("cool-name_42") is True

    def test_rejects_too_short(self):
        assert is_valid_username("ab") is False

    def test_rejects_too_long(self):
        assert is_valid_username("a" * 41) is False

    def test_accepts_max_length(self):
        assert is_valid_username("a" * 40) is True

    def test_rejects_spaces(self):
        assert is_valid_username("has space") is False

    def test_rejects_special_characters(self):
        assert is_valid_username("name@domain") is False
