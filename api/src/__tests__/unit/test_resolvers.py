"""
Tests for resolver clients -- iTunes, Last.fm, MusicBrainz. HTTP mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clients.resolvers import itunes, lastfm, musicbrainz


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


class TestMusicbrainzLookupUrl:
    async def test_resolves_spotify_url_from_relations(self):
        # First call: ISRC search -> recording mbid.
        # Second call: recording -> url-rels.
        responses = [
            _resp(json_data={"recordings": [{"id": "mb-uuid-1"}]}),
            _resp(json_data={
                "relations": [
                    {"url": {"resource": "https://open.spotify.com/track/SPID123"}}
                ]
            }),
        ]
        client = MagicMock()
        client.get = AsyncMock(side_effect=responses)
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("GBTDG0900141", "spotify")
        assert url == "https://open.spotify.com/track/SPID123"

    async def test_resolves_apple_music_url(self):
        responses = [
            _resp(json_data={"recordings": [{"id": "mb-2"}]}),
            _resp(json_data={
                "relations": [
                    {"url": {"resource": "https://music.apple.com/us/song/_/9"}}
                ]
            }),
        ]
        client = MagicMock()
        client.get = AsyncMock(side_effect=responses)
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("X1234567890", "appleMusic")
        assert url == "https://music.apple.com/us/song/_/9"

    async def test_returns_none_for_unsupported_platform(self):
        url = await musicbrainz.lookup_url("ANY12345678", "beatport")
        assert url is None

    async def test_returns_none_when_no_recordings(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={"recordings": []}))
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("XX1234567890", "spotify")
        assert url is None

    async def test_returns_none_when_relations_have_no_match(self):
        responses = [
            _resp(json_data={"recordings": [{"id": "mb-3"}]}),
            _resp(json_data={
                "relations": [
                    {"url": {"resource": "https://example.com/unrelated"}}
                ]
            }),
        ]
        client = MagicMock()
        client.get = AsyncMock(side_effect=responses)
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("XX1234567890", "spotify")
        assert url is None

    async def test_returns_none_on_http_error(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(status=500))
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("XX1234567890", "spotify")
        assert url is None

    async def test_returns_none_on_client_exception(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("clients.resolvers.musicbrainz._get_client", return_value=client):
            url = await musicbrainz.lookup_url("XX1234567890", "spotify")
        assert url is None
