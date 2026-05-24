"""
Tests for clients.resolvers.odesli -- routing rules + pure extractors.
"""

from clients.resolvers import odesli


class TestShouldSkip:
    def test_skips_unsupported_target(self):
        assert odesli.should_skip("spotify", "beatport") is True
        assert odesli.should_skip("spotify", "bandcamp") is True

    def test_skips_unreliable_source(self):
        assert odesli.should_skip("soundcloud", "spotify") is True

    def test_allows_supported_pair(self):
        assert odesli.should_skip("spotify", "deezer") is False
        assert odesli.should_skip("appleMusic", "tidal") is False

    def test_allows_no_source(self):
        assert odesli.should_skip(None, "spotify") is False


class TestExtractUrl:
    def test_returns_platform_url(self):
        data = {"linksByPlatform": {"spotify": {"url": "https://open.spotify.com/track/x"}}}
        assert odesli.extract_url(data, "spotify") == "https://open.spotify.com/track/x"

    def test_returns_none_when_platform_missing(self):
        assert odesli.extract_url({"linksByPlatform": {}}, "spotify") is None

    def test_returns_none_when_url_missing(self):
        data = {"linksByPlatform": {"spotify": {}}}
        assert odesli.extract_url(data, "spotify") is None


class TestExtractMetadata:
    def test_returns_first_titled_entity(self):
        data = {"entitiesByUniqueId": {
            "a": {"title": "Hello", "artistName": "Adele"},
            "b": {"title": "Other", "artistName": "X"},
        }}
        title, artist = odesli.extract_metadata(data)
        assert title == "Hello"
        assert artist == "Adele"

    def test_skips_entities_without_title(self):
        data = {"entitiesByUniqueId": {
            "a": {"artistName": "Empty"},
            "b": {"title": "Found", "artistName": "Real"},
        }}
        title, artist = odesli.extract_metadata(data)
        assert title == "Found"
        assert artist == "Real"

    def test_returns_none_when_no_entities(self):
        assert odesli.extract_metadata({"entitiesByUniqueId": {}}) == (None, None)
