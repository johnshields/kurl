"""
Tests for utils.kurlname -- music-noun name generation from faker-music.
"""

from unittest.mock import patch

from utils.kurlname import _nouns, generate


class TestGenerate:
    def test_is_an_adjective_then_a_music_noun(self):
        nouns = set(_nouns())
        for _ in range(50):
            adjective, noun = generate().split("-")
            assert adjective.isalpha()
            assert noun in nouns

    def test_two_calls_are_very_likely_different(self):
        assert len({generate() for _ in range(20)}) > 1

    def test_generated_names_fit_the_username_limit(self):
        assert all(len(generate()) <= 40 for _ in range(500))

    def test_falls_back_to_a_coolname_slug_when_faker_music_is_unavailable(self):
        with patch("utils.kurlname._nouns", return_value=()):
            assert len(generate().split("-")) == 2


class TestNouns:
    def test_are_unique_lowercase_letters(self):
        nouns = _nouns()
        assert len(nouns) == len(set(nouns))
        assert all(w.isascii() and w.isalpha() and w.islower() for w in nouns)

    def test_are_a_large_pool(self):
        assert len(_nouns()) > 500

    def test_exclude_the_stoplist(self):
        assert not {"leona", "marfa", "raison", "sambal"} & set(_nouns())
