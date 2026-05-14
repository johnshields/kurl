"""
Tests for utils.url -- tracking param stripping.
"""

from utils.url import normalise_url


class TestNormaliseUrl:
    def test_strips_si_tracking_param(self):
        url = "https://open.spotify.com/track/abc?si=xyz123"
        assert normalise_url(url) == "https://open.spotify.com/track/abc"

    def test_strips_utm_params(self):
        url = "https://example.com/path?utm_source=twitter&utm_medium=social"
        assert normalise_url(url) == "https://example.com/path"

    def test_strips_fbclid_gclid(self):
        url = "https://example.com/track?fbclid=abc&gclid=xyz"
        assert normalise_url(url) == "https://example.com/track"

    def test_preserves_functional_params(self):
        # Apple Music needs the i= param -- it identifies the track.
        url = "https://music.apple.com/us/album/x/123?i=456&si=tracking"
        result = normalise_url(url)
        assert "i=456" in result
        assert "si=tracking" not in result

    def test_preserves_url_without_query(self):
        url = "https://open.spotify.com/track/abc"
        assert normalise_url(url) == url

    def test_preserves_path_and_fragment(self):
        url = "https://example.com/foo/bar?si=x#section"
        result = normalise_url(url)
        assert "/foo/bar" in result
        assert "#section" in result

    def test_handles_multiple_values_of_same_tracking_key(self):
        url = "https://example.com/t?si=a&si=b&keep=1"
        result = normalise_url(url)
        assert "si=" not in result
        assert "keep=1" in result
