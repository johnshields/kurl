"""
Tests for clients.resolvers.itunes.canonicalise -- the iTunes Search API is
known to return HTML-entity-escaped trackName/artistName for some tracks.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from clients.resolvers import itunes


class TestCanonicalise:
    async def test_decodes_html_entities(self):
        with patch(
            "clients.resolvers.itunes._search_one",
            AsyncMock(return_value={"trackName": "These Things Will Come&#39;", "artistName": "Tom &amp; Jerry"}),
        ):
            title, artist = await itunes.canonicalise("query title", "query artist")
        assert title == "These Things Will Come'"
        assert artist == "Tom & Jerry"

    async def test_passes_through_on_no_match(self):
        with patch("clients.resolvers.itunes._search_one", AsyncMock(return_value=None)):
            title, artist = await itunes.canonicalise("Original", "Artist")
        assert (title, artist) == ("Original", "Artist")


class TestSearchFailuresAreNotCached:
    async def test_rate_limit_is_retried_not_memoised(self):
        itunes._search_cache.clear()
        limited = SimpleNamespace(status_code=429, text="")
        ok = SimpleNamespace(status_code=200, text="", json=lambda: {"results": [{"trackName": "T"}]})
        client = SimpleNamespace(get=AsyncMock(side_effect=[limited, ok]))

        with patch("clients.resolvers.itunes._get_client", return_value=client):
            assert await itunes._search_one("Song", "Artist") is None
            assert (await itunes._search_one("Song", "Artist"))["trackName"] == "T"
        itunes._search_cache.clear()
