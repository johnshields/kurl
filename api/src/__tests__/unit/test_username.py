"""
Tests for utils.auth.username -- generation and validation.
"""

from unittest.mock import patch

from randomname import util

from utils.auth.username import generate_username, generate_username_with_suffix, is_valid_username


class TestGenerateUsername:
    def test_generates_a_valid_username(self):
        assert is_valid_username(generate_username())

    def test_two_calls_are_very_likely_different(self):
        # The word pool is large enough that a collision here would
        # indicate something is broken, not bad luck.
        names = {generate_username() for _ in range(20)}
        assert len(names) > 1

    def test_noun_is_a_music_word(self):
        nouns = set(util.get_groups_list(["n/music_instruments", "n/music_theory"]))
        for _ in range(50):
            adjective, noun = generate_username().split("-")
            assert noun in nouns

    def test_falls_back_to_coolname_when_randomname_fails(self):
        with patch("randomname.generate", side_effect=RuntimeError("no word files")):
            assert is_valid_username(generate_username())


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
