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


class TestItunesCanonicalise:
    def setup_method(self):
        itunes._search_cache.clear()

    async def test_snaps_to_catalogue_values(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={
            "results": [{"trackName": "Can't Stand To Lose", "artistName": "HAAi"}]
        }))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            t, a = await itunes.canonicalise("cant stand to lose", "haai")
        assert (t, a) == ("Can't Stand To Lose", "HAAi")

    async def test_passthrough_on_miss(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={"results": []}))
        with patch("clients.resolvers.itunes._get_client", return_value=client):
            t, a = await itunes.canonicalise("Unknown Track", "Nobody")
        assert (t, a) == ("Unknown Track", "Nobody")


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
    async def test_extracts_first_track_from_serp(self):
        html = '<a href="https://open.spotify.com/track/abcDEF123456ghi789JKL0">first</a>'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text=html))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await spotify_search.search_track_url("Hello", "Adele")
        assert url == "https://open.spotify.com/track/abcDEF123456ghi789JKL0"

    async def test_returns_none_when_no_match(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text="<html>no results</html>"))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await spotify_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_when_title_or_artist_missing(self):
        assert await spotify_search.search_track_url("", "Adele") is None
        assert await spotify_search.search_track_url("Hello", "") is None

    async def test_returns_none_on_http_error(self):
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(status=429))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await spotify_search.search_track_url("x", "y")
        assert url is None


class TestBeatportSearch:
    async def test_extracts_first_track_url(self):
        from clients.resolvers import beatport_search
        html = '<a href="https://www.beatport.com/track/cant-stand-to-lose/20044066">first</a>'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text=html))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await beatport_search.search_track_url("Can't Stand To Lose", "HAAi")
        assert url == "https://www.beatport.com/track/cant-stand-to-lose/20044066"

    async def test_returns_none_when_no_match(self):
        from clients.resolvers import beatport_search
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text="<html>nope</html>"))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await beatport_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_on_missing_inputs(self):
        from clients.resolvers import beatport_search
        assert await beatport_search.search_track_url("", "y") is None
        assert await beatport_search.search_track_url("x", "") is None

    async def test_rejects_mismatched_slug(self):
        from clients.resolvers import beatport_search
        html = '<a href="https://www.beatport.com/track/happiness/26921777">unrelated</a>'
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(text=html))
        with patch("clients.resolvers._serp._client", return_value=client):
            url = await beatport_search.search_track_url("Comes Together", "HAAi")
        assert url is None


class TestBandcampSearch:
    async def test_returns_first_track_url(self):
        from clients.resolvers import bandcamp_search
        client = MagicMock()
        client.post = AsyncMock(return_value=_resp(json_data={
            "auto": {"results": [
                {"item_url_path": "https://artist.bandcamp.com/album/foo"},
                {"item_url_path": "https://artist.bandcamp.com/track/foo"},
            ]}
        }))
        with patch("clients.resolvers.bandcamp_search._get_client", return_value=client):
            url = await bandcamp_search.search_track_url("foo", "artist")
        assert url == "https://artist.bandcamp.com/track/foo"

    async def test_returns_none_when_no_track_in_results(self):
        from clients.resolvers import bandcamp_search
        client = MagicMock()
        client.post = AsyncMock(return_value=_resp(json_data={"auto": {"results": []}}))
        with patch("clients.resolvers.bandcamp_search._get_client", return_value=client):
            url = await bandcamp_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_on_http_error(self):
        from clients.resolvers import bandcamp_search
        client = MagicMock()
        client.post = AsyncMock(return_value=_resp(status=500))
        with patch("clients.resolvers.bandcamp_search._get_client", return_value=client):
            url = await bandcamp_search.search_track_url("x", "y")
        assert url is None

    async def test_returns_none_on_exception(self):
        from clients.resolvers import bandcamp_search
        client = MagicMock()
        client.post = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("clients.resolvers.bandcamp_search._get_client", return_value=client):
            url = await bandcamp_search.search_track_url("x", "y")
        assert url is None


class TestGeniusResolver:
    def _patch_settings(self, monkeypatch):
        from app import config as cfg
        monkeypatch.setattr(cfg.settings, "GENIUS_ACCESS_TOKEN", "test-token", raising=False)

    @pytest.fixture
    def settings_with_token(self, monkeypatch):
        from app import config as cfg
        original = cfg.settings._get
        monkeypatch.setattr(cfg.settings, "_get", lambda k, d=None: "test-token" if k == "GENIUS_ACCESS_TOKEN" else original(k, d))

    async def test_returns_spotify_url_from_song_media(self, settings_with_token):
        from clients.resolvers import genius
        search_resp = _resp(json_data={"response": {"hits": [{"result": {"id": 42}}]}})
        song_resp = _resp(json_data={
            "response": {"song": {"media": [
                {"provider": "spotify", "url": "https://open.spotify.com/track/G123"},
                {"provider": "apple_music", "url": "https://music.apple.com/us/song/_/99"},
            ]}}
        })
        client = MagicMock()
        client.get = AsyncMock(side_effect=[search_resp, song_resp])
        with patch("clients.resolvers.genius._get_client", return_value=client):
            url = await genius.spotify_url("Hello", "Adele")
        assert url == "https://open.spotify.com/track/G123"

    async def test_returns_none_when_no_hits(self, settings_with_token):
        from clients.resolvers import genius
        client = MagicMock()
        client.get = AsyncMock(return_value=_resp(json_data={"response": {"hits": []}}))
        with patch("clients.resolvers.genius._get_client", return_value=client):
            url = await genius.spotify_url("x", "y")
        assert url is None

    async def test_returns_none_when_platform_missing(self, settings_with_token):
        from clients.resolvers import genius
        search_resp = _resp(json_data={"response": {"hits": [{"result": {"id": 7}}]}})
        song_resp = _resp(json_data={"response": {"song": {"media": [
            {"provider": "soundcloud", "url": "https://soundcloud.com/x/y"}
        ]}}})
        client = MagicMock()
        client.get = AsyncMock(side_effect=[search_resp, song_resp])
        with patch("clients.resolvers.genius._get_client", return_value=client):
            url = await genius.spotify_url("x", "y")
        assert url is None

    async def test_returns_none_without_token(self, monkeypatch):
        from clients.resolvers import genius
        from app import config as cfg
        monkeypatch.setattr(cfg.settings, "_get", lambda k, d=None: None)
        url = await genius.spotify_url("x", "y")
        assert url is None
