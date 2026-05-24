"""
Tests for utils.url.short_links -- detection + resolution. HTTP mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from utils.url import short_links


def _resp(final_url: str, text: str = "", status: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.url = final_url
    return r


class TestIsShortLink:
    def test_spotify_link(self):
        assert short_links.is_short_link("https://spotify.link/abc123") is True

    def test_deezer_short(self):
        assert short_links.is_short_link("https://dzr.page.link/xyz") is True

    def test_soundcloud_on(self):
        assert short_links.is_short_link("https://on.soundcloud.com/abc") is True

    def test_canonical_url_not_short(self):
        assert short_links.is_short_link("https://open.spotify.com/track/x") is False

    def test_empty_url(self):
        assert short_links.is_short_link("") is False


class TestResolveShortLink:
    async def test_returns_final_url_when_redirect_lands_on_canonical(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp("https://open.spotify.com/track/abc"))
        with patch("utils.url.short_links._get_client", return_value=client):
            result = await short_links.resolve_short_link("https://spotify.link/x")
        assert result == "https://open.spotify.com/track/abc"

    async def test_extracts_og_url_when_still_on_short_host(self):
        html = '<meta property="og:url" content="https://open.spotify.com/track/realid">'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp("https://spotify.link/x", text=html))
        with patch("utils.url.short_links._get_client", return_value=client):
            result = await short_links.resolve_short_link("https://spotify.link/x")
        assert result == "https://open.spotify.com/track/realid"

    async def test_extracts_meta_refresh_when_no_og_url(self):
        html = '<meta http-equiv="refresh" content="0;url=https://open.spotify.com/track/refresh1">'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp("https://spotify.link/x", text=html))
        with patch("utils.url.short_links._get_client", return_value=client):
            result = await short_links.resolve_short_link("https://spotify.link/x")
        assert result == "https://open.spotify.com/track/refresh1"

    async def test_returns_input_when_nothing_found(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp("https://spotify.link/x", text="<html></html>"))
        with patch("utils.url.short_links._get_client", return_value=client):
            result = await short_links.resolve_short_link("https://spotify.link/x")
        assert result == "https://spotify.link/x"

    async def test_returns_input_on_exception(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=RuntimeError("net"))
        with patch("utils.url.short_links._get_client", return_value=client):
            result = await short_links.resolve_short_link("https://spotify.link/x")
        assert result == "https://spotify.link/x"
