"""
Tests for utils.search_url -- template-driven search URL fallbacks.
"""

from utils.search_url import build_search_url


class TestBuildSearchUrl:
    def test_spotify(self):
        url = build_search_url("spotify", "Hello", "Adele")
        assert url == "https://open.spotify.com/search/Hello%20Adele"

    def test_apple_music_uses_term_query_param(self):
        url = build_search_url("appleMusic", "Hello", "Adele")
        # /us/ prefix avoids Apple's redirect which converts %20 into literal +
        assert url == "https://music.apple.com/us/search?term=Hello%20Adele"

    def test_youtube_music(self):
        url = build_search_url("youtubeMusic", "Hello", "Adele")
        assert url == "https://music.youtube.com/search?q=Hello%20Adele"

    def test_deezer(self):
        url = build_search_url("deezer", "Hello", "Adele")
        assert url == "https://www.deezer.com/search/Hello%20Adele"

    def test_tidal(self):
        url = build_search_url("tidal", "Hello", "Adele")
        assert url == "https://tidal.com/search/Hello%20Adele"

    def test_amazon(self):
        url = build_search_url("amazonMusic", "Hello", "Adele")
        assert url == "https://music.amazon.com/search/Hello%20Adele"

    def test_pandora(self):
        url = build_search_url("pandora", "Hello", "Adele")
        assert url == "https://www.pandora.com/search/Hello%20Adele"

    def test_unknown_platform_returns_none(self):
        assert build_search_url("foobar", "Hello", "Adele") is None

    def test_both_empty_returns_none(self):
        assert build_search_url("spotify", None, None) is None

    def test_only_title_is_sufficient(self):
        url = build_search_url("spotify", "Hello", None)
        assert url == "https://open.spotify.com/search/Hello"

    def test_only_artist_is_sufficient(self):
        url = build_search_url("spotify", None, "Adele")
        assert url == "https://open.spotify.com/search/Adele"

    def test_special_chars_url_encoded(self):
        url = build_search_url("spotify", "Can't Stand To Lose", "HAAi")
        assert "Can%27t" in url
