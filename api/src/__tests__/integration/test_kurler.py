"""
Tests for utils.kurler -- the orchestrator that resolves a source url to a target
platform via ISRC/UPC/name, falling back to metadata search.

Platform clients are mocked; these tests verify the fallback chain, not the APIs.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.kurler import kurl
from utils.url.url_parser import ParsedMusicUrl


def _mock_client() -> MagicMock:
    """A MagicMock that passes `is_configured()` and supports all client functions."""
    m = MagicMock()
    m.is_configured.return_value = True
    return m


@pytest.fixture
def mock_clients():
    """Replace the kurler's _CLIENTS registry with mocks."""
    clients = {
        "spotify": _mock_client(),
        "appleMusic": _mock_client(),
        "deezer": _mock_client(),
        "tidal": _mock_client(),
    }
    with patch.dict("utils.kurler._CLIENTS", clients, clear=True):
        yield clients


class TestTargetNotConfigured:
    async def test_returns_none_when_target_has_no_client(self, mock_clients):
        """amazonMusic has no client -- kurler should bail out fast."""
        source = ParsedMusicUrl("spotify", "track", "abc")
        # _CLIENTS only contains the four mocked ones -- amazonMusic is absent.
        result = await kurl(source, "amazonMusic")
        assert result is None


class TestIsrcHappyPath:
    async def test_spotify_to_deezer_via_isrc(self, mock_clients):
        """Source ISRC lookup succeeds, target ISRC search returns a hit."""
        source_track = {"isrc": "GBX1234", "title": "Hello", "artists": [{"name": "Adele"}]}
        target_track = {"title": "Hello", "link": "https://deezer.com/track/999"}

        mock_clients["spotify"].get_track = AsyncMock(return_value=source_track)
        mock_clients["spotify"].extract_isrc.return_value = "GBX1234"
        mock_clients["spotify"].extract_metadata.return_value = ("Hello", "Adele")

        mock_clients["deezer"].search_by_isrc = AsyncMock(return_value=target_track)
        mock_clients["deezer"].extract_track_url.return_value = "https://deezer.com/track/999"
        mock_clients["deezer"].extract_metadata.return_value = ("Hello", "Adele")

        source = ParsedMusicUrl("spotify", "track", "abc")
        result = await kurl(source, "deezer")

        assert result is not None
        assert result.url == "https://deezer.com/track/999"
        assert result.title == "Hello"
        assert result.artist == "Adele"
        assert result.via == "isrc"


class TestIsrcMissFallsBackToMetadataSearch:
    async def test_when_source_has_no_isrc_metadata_search_is_used(self, mock_clients):
        """Source returns no ISRC -- should scrape metadata and search target."""
        # Source is YouTube -- no client -- so _lookup_identifier short-circuits.
        # The fallback scrapes metadata and calls target.search_track.
        target_track = {"link": "https://deezer.com/track/777"}

        mock_clients["deezer"].search_track = AsyncMock(return_value=target_track)
        mock_clients["deezer"].extract_track_url.return_value = "https://deezer.com/track/777"
        mock_clients["deezer"].extract_metadata.return_value = ("Hello", "Adele")

        source = ParsedMusicUrl("youtubeMusic", "track", "abc123")

        with patch("utils.kurler.metadata.fetch_metadata", new=AsyncMock(return_value=("Hello", "Adele", None))):
            result = await kurl(source, "deezer")

        assert result is not None
        assert result.url == "https://deezer.com/track/777"
        assert result.via == "search_api"


class TestMetadataSearchWithoutMetadata:
    async def test_returns_none_when_no_title_or_artist(self, mock_clients):
        """If neither ISRC nor metadata yields a title+artist, give up."""
        source = ParsedMusicUrl("youtubeMusic", "track", "abc")

        with patch("utils.kurler.metadata.fetch_metadata", new=AsyncMock(return_value=(None, None, None))):
            result = await kurl(source, "deezer")

        assert result is None


class TestAlbumViaUpc:
    async def test_upc_lookup_and_search(self, mock_clients):
        mock_clients["spotify"].get_album = AsyncMock(return_value={"external_ids": {"upc": "UPC123"}})
        mock_clients["spotify"].extract_upc.return_value = "UPC123"
        mock_clients["spotify"].extract_album_metadata.return_value = ("My Album", "Adele")

        mock_clients["deezer"].search_by_upc = AsyncMock(return_value={"link": "https://deezer.com/album/9"})
        mock_clients["deezer"].extract_album_url.return_value = "https://deezer.com/album/9"
        mock_clients["deezer"].extract_album_metadata.return_value = ("My Album", "Adele")

        source = ParsedMusicUrl("spotify", "album", "xyz")
        result = await kurl(source, "deezer")

        assert result is not None
        assert result.url == "https://deezer.com/album/9"
        assert result.via == "upc"


class TestArtistByName:
    async def test_artist_name_match(self, mock_clients):
        mock_clients["spotify"].get_artist = AsyncMock(return_value={"name": "Adele"})
        mock_clients["spotify"].extract_artist_name.return_value = "Adele"

        mock_clients["deezer"].search_artist = AsyncMock(return_value={"id": 123})
        mock_clients["deezer"].extract_artist_url.return_value = "https://deezer.com/artist/123"

        source = ParsedMusicUrl("spotify", "artist", "A1")
        result = await kurl(source, "deezer")

        assert result is not None
        assert result.url == "https://deezer.com/artist/123"
        assert result.via == "name"
        assert result.title == "Adele"


class TestAppleStorefrontThreading:
    async def test_apple_source_passes_storefront_kwarg(self, mock_clients):
        """When source is Apple Music, the storefront kwarg should be threaded."""
        mock_clients["appleMusic"].get_track = AsyncMock(return_value={})
        mock_clients["appleMusic"].extract_isrc.return_value = None
        mock_clients["appleMusic"].extract_metadata.return_value = (None, None)

        source = ParsedMusicUrl("appleMusic", "track", "1234", country="gb")
        with patch("utils.kurler.metadata.fetch_metadata", new=AsyncMock(return_value=(None, None, None))):
            await kurl(source, "spotify")

        mock_clients["appleMusic"].get_track.assert_awaited_once_with("1234", storefront="gb")


class TestClientFailurePropagation:
    async def test_client_raising_does_not_crash_kurler(self, mock_clients):
        """Any unexpected exception from a client should return None, not bubble."""
        mock_clients["spotify"].get_track = AsyncMock(side_effect=RuntimeError("boom"))

        source = ParsedMusicUrl("spotify", "track", "abc")
        with patch("utils.kurler.metadata.fetch_metadata", new=AsyncMock(return_value=(None, None, None))):
            result = await kurl(source, "deezer")

        assert result is None


class TestRescuePath:
    """Rescue chain: iTunes for Apple, Last.fm + DDG search for Spotify."""

    async def test_apple_rescue_via_itunes(self, mock_clients):
        mock_clients["spotify"].get_track = AsyncMock(return_value={})
        mock_clients["spotify"].extract_isrc.return_value = "ISRC0001"
        mock_clients["spotify"].extract_metadata.return_value = ("Hello", "Adele")
        mock_clients["appleMusic"].search_by_isrc = AsyncMock(return_value=None)

        source = ParsedMusicUrl("spotify", "track", "abc")
        with patch(
            "utils.kurler.itunes.fetch_apple_music_url",
            new=AsyncMock(return_value="https://music.apple.com/us/song/_/42"),
        ):
            result = await kurl(source, "appleMusic")

        assert result is not None
        assert result.url == "https://music.apple.com/us/song/_/42"
        assert result.via == "isrc"

    async def test_spotify_rescue_via_lastfm(self, mock_clients):
        mock_clients["appleMusic"].get_track = AsyncMock(return_value={})
        mock_clients["appleMusic"].extract_isrc.return_value = "ISRC0003"
        mock_clients["appleMusic"].extract_metadata.return_value = ("Hello", "Adele")
        mock_clients["spotify"].search_by_isrc = AsyncMock(return_value=None)

        source = ParsedMusicUrl("appleMusic", "track", "1234", country="us")
        with patch(
            "utils.kurler.spotify_search.search_track_url",
            new=AsyncMock(return_value=None),
        ), patch(
            "utils.kurler.lastfm.spotify_url",
            new=AsyncMock(return_value="https://open.spotify.com/track/LF999"),
        ):
            result = await kurl(source, "spotify")

        assert result is not None
        assert result.url == "https://open.spotify.com/track/LF999"

    async def test_spotify_rescue_via_ddg(self, mock_clients):
        mock_clients["appleMusic"].get_track = AsyncMock(return_value={})
        mock_clients["appleMusic"].extract_isrc.return_value = "ISRC0005"
        mock_clients["appleMusic"].extract_metadata.return_value = ("Hello", "Adele")
        mock_clients["spotify"].search_by_isrc = AsyncMock(return_value=None)

        source = ParsedMusicUrl("appleMusic", "track", "1234", country="us")
        with patch(
            "utils.kurler.lastfm.spotify_url",
            new=AsyncMock(return_value=None),
        ), patch(
            "utils.kurler.spotify_search.search_track_url",
            new=AsyncMock(return_value="https://open.spotify.com/track/DDG123"),
        ):
            result = await kurl(source, "spotify")

        assert result is not None
        assert result.url == "https://open.spotify.com/track/DDG123"

    async def test_non_rescue_target_skips_rescue(self, mock_clients):
        """Deezer is not in RESCUE_PLATFORMS -- rescue chain must not be invoked."""
        mock_clients["spotify"].get_track = AsyncMock(return_value={})
        mock_clients["spotify"].extract_isrc.return_value = "ISRC0004"
        mock_clients["spotify"].extract_metadata.return_value = ("Hello", "Adele")
        mock_clients["deezer"].search_by_isrc = AsyncMock(return_value=None)
        mock_clients["deezer"].search_track = AsyncMock(return_value=None)

        itunes_mock = AsyncMock(return_value="should-not-be-used")
        lastfm_mock = AsyncMock(return_value="should-not-be-used")

        source = ParsedMusicUrl("spotify", "track", "abc")
        with patch("utils.kurler.itunes.fetch_apple_music_url", new=itunes_mock), \
             patch("utils.kurler.lastfm.spotify_url", new=lastfm_mock):
            await kurl(source, "deezer")

        itunes_mock.assert_not_awaited()
        lastfm_mock.assert_not_awaited()


class TestRescueWithoutTargetClient:
    async def test_apple_rescue_runs_when_apple_client_unconfigured(self, mock_clients):
        """Apple client absent from _CLIENTS -- iTunes rescue should still run."""
        # appleMusic deliberately not in the mocked _CLIENTS for this test.
        clients_without_apple = {
            "spotify": mock_clients["spotify"],
            "deezer": mock_clients["deezer"],
        }
        mock_clients["spotify"].get_track = AsyncMock(return_value={})
        mock_clients["spotify"].extract_isrc.return_value = "ISRC0099"
        mock_clients["spotify"].extract_metadata.return_value = ("Hello", "Adele")

        source = ParsedMusicUrl("spotify", "track", "abc")
        with patch.dict("utils.kurler._CLIENTS", clients_without_apple, clear=True), \
             patch(
                 "utils.kurler.itunes.fetch_apple_music_url",
                 new=AsyncMock(return_value="https://music.apple.com/us/song/_/99"),
             ):
            result = await kurl(source, "appleMusic")

        assert result is not None
        assert result.url == "https://music.apple.com/us/song/_/99"
