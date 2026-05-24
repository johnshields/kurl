"""
Tests for resolver clients -- iTunes, Last.fm, DDG Spotify search. HTTP mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clients.resolvers import itunes, lastfm, spotify_search


def _resp(status: int = 200, json_data: dict | None = None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data or {}
    r.text = text
    return r


class TestItunesFetchAppleMusicUrl:
    def setup_method(self):
        itunes._search_cache.clear()

    async def test_returns_trackviewurl(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={
            "results": [{"trackViewUrl": "https://music.apple.com/us/song/_/12345"}]
        }))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            url = await itunes.fetch_apple_music_url("Hello", "Adele")
        assert url == "https://music.apple.com/us/song/_/12345"

    async def test_returns_none_when_no_results(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={"results": []}))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            url = await itunes.fetch_apple_music_url("nope", "nobody")
        assert url is None

    async def test_returns_none_when_title_missing(self):
        assert await itunes.fetch_apple_music_url(None, "Adele") is None

    async def test_returns_none_on_http_error(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(status=503))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            url = await itunes.fetch_apple_music_url("x", "y")
        assert url is None


class TestItunesFetchArtwork:
    def setup_method(self):
        itunes._search_cache.clear()

    async def test_upgrades_resolution_to_600x600(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={
            "results": [{"artworkUrl100": "https://is1.mzstatic.com/img/100x100bb.jpg"}]
        }))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            art = await itunes.fetch_artwork("Hello", "Adele")
        assert art == "https://is1.mzstatic.com/img/600x600bb.jpg"

    async def test_returns_none_when_artwork_missing(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={"results": [{}]}))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            art = await itunes.fetch_artwork("x", "y")
        assert art is None


class TestItunesMemoisation:
    def setup_method(self):
        itunes._search_cache.clear()

    async def test_artwork_and_url_share_one_http_call(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={
            "results": [{
                "artworkUrl100": "https://is1.mzstatic.com/img/100x100bb.jpg",
                "trackViewUrl": "https://music.apple.com/us/song/_/1",
            }]
        }))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            await itunes.fetch_artwork("Hello", "Adele")
            await itunes.fetch_apple_music_url("Hello", "Adele")
        assert client.get.await_count == 1


class TestLastfmSpotifyUrl:
    async def test_extracts_spotify_uri_from_html(self):
        html = 'random html with spotify:track:abc123DEF456ghi789JKL0 embedded'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text=html))
        with patch("clients.resolvers.lastfm._get_client", return_value=client):
            url = await lastfm.spotify_url("Hello", "Adele")
        assert url == "https://open.spotify.com/track/abc123DEF456ghi789JKL0"

    async def test_returns_none_when_no_uri_in_html(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text="<html>no spotify uri</html>"))
        with patch("clients.resolvers.lastfm._get_client", return_value=client):
            url = await lastfm.spotify_url("x", "y")
        assert url is None

    async def test_returns_none_when_title_or_artist_missing(self):
        assert await lastfm.spotify_url("", "Adele") is None
        assert await lastfm.spotify_url("Hello", "") is None

    async def test_returns_none_on_http_error(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(status=404))
        with patch("clients.resolvers.lastfm._get_client", return_value=client):
            url = await lastfm.spotify_url("x", "y")
        assert url is None

    async def test_returns_none_on_client_exception(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("clients.resolvers.lastfm._get_client", return_value=client):
            url = await lastfm.spotify_url("x", "y")
        assert url is None




class TestSpotifySearchScrape:
    async def test_extracts_first_track_from_ddg_serp(self):
        html = '''<html>
        <a href="https://open.spotify.com/track/abcDEF123456ghi789JKL0">first</a>
        <a href="https://open.spotify.com/track/zzzZZZ987654321ABCdef0">second</a>
        </html>'''
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text=html))
        with patch("clients.resolvers.spotify_search._get_client", return_value=client):
            url = await spotify_search.search_track_url("Hello", "Adele")
        assert url == "https://open.spotify.com/track/abcDEF123456ghi789JKL0"

    async def test_returns_none_when_no_match(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text="<html>no results</html>"))
        with patch("clients.resolvers.spotify_search._get_client", return_value=client):
            url = await spotify_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_when_title_or_artist_missing(self):
        assert await spotify_search.search_track_url("", "Adele") is None
        assert await spotify_search.search_track_url("Hello", "") is None

    async def test_returns_none_on_http_error(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(status=429))
        with patch("clients.resolvers.spotify_search._get_client", return_value=client):
            url = await spotify_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_on_exception(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("clients.resolvers.spotify_search._get_client", return_value=client):
            url = await spotify_search.search_track_url("x", "y")
        assert url is None
