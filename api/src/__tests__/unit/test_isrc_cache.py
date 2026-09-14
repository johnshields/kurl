"""
Tests for utils.kurler._search_by_identifier's typed ISRC/UPC cache layer --
positive and negative hits on separate TTLs, keyed by (via, identifier, target).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants import ISRC_CACHE_NEGATIVE_TTL, ISRC_CACHE_POSITIVE_TTL
from utils.kurler import _search_by_identifier


def _mock_client() -> MagicMock:
    m = MagicMock()
    m.is_configured.return_value = True
    return m


class TestCacheHit:
    async def test_positive_hit_skips_the_target_search(self):
        client = _mock_client()
        client.search_by_isrc = AsyncMock(side_effect=AssertionError("should not be called"))
        cached = json.dumps({"url": "https://deezer.com/track/999", "title": "Hello", "artist": "Adele"})

        with patch.dict("utils.kurler._CLIENTS", {"deezer": client}, clear=True), patch(
            "utils.kurler.cache.get", new=AsyncMock(return_value=cached)
        ):
            result = await _search_by_identifier(
                "deezer", "GBX1234", search="search_by_isrc", url_getter="extract_track_url", via="isrc"
            )

        assert result is not None
        assert result.url == "https://deezer.com/track/999"
        assert result.title == "Hello"
        assert result.artist == "Adele"
        assert result.via == "isrc"

    async def test_negative_hit_skips_the_target_search(self):
        client = _mock_client()
        client.search_by_isrc = AsyncMock(side_effect=AssertionError("should not be called"))

        with patch.dict("utils.kurler._CLIENTS", {"deezer": client}, clear=True), patch(
            "utils.kurler.cache.get", new=AsyncMock(return_value="null")
        ):
            result = await _search_by_identifier(
                "deezer", "GBX1234", search="search_by_isrc", url_getter="extract_track_url", via="isrc"
            )

        assert result is None


class TestCacheMiss:
    async def test_a_match_is_cached_positive_with_a_long_ttl(self):
        client = _mock_client()
        client.search_by_isrc = AsyncMock(return_value={"link": "https://deezer.com/track/999"})
        client.extract_track_url.return_value = "https://deezer.com/track/999"
        client.extract_metadata.return_value = ("Hello", "Adele")
        cache_set = AsyncMock()

        with patch.dict("utils.kurler._CLIENTS", {"deezer": client}, clear=True), patch(
            "utils.kurler.cache.get", new=AsyncMock(return_value=None)
        ), patch("utils.kurler.cache.set", new=cache_set):
            result = await _search_by_identifier(
                "deezer", "GBX1234", search="search_by_isrc", url_getter="extract_track_url", via="isrc"
            )

        assert result is not None
        cache_set.assert_awaited_once()
        key, payload = cache_set.await_args.args
        assert key == "isrc:GBX1234:deezer"
        assert json.loads(payload) == {"url": "https://deezer.com/track/999", "title": "Hello", "artist": "Adele"}
        assert cache_set.await_args.kwargs["ttl"] == ISRC_CACHE_POSITIVE_TTL

    async def test_a_miss_is_cached_negative_with_a_short_ttl(self):
        client = _mock_client()
        client.search_by_isrc = AsyncMock(return_value=None)
        cache_set = AsyncMock()

        with patch.dict("utils.kurler._CLIENTS", {"deezer": client}, clear=True), patch(
            "utils.kurler.cache.get", new=AsyncMock(return_value=None)
        ), patch("utils.kurler.cache.set", new=cache_set):
            result = await _search_by_identifier(
                "deezer", "GBX1234", search="search_by_isrc", url_getter="extract_track_url", via="isrc"
            )

        assert result is None
        cache_set.assert_awaited_once_with("isrc:GBX1234:deezer", "null", ttl=ISRC_CACHE_NEGATIVE_TTL)

    async def test_a_transient_error_is_not_cached(self):
        client = _mock_client()
        client.search_by_isrc = AsyncMock(side_effect=RuntimeError("network blip"))
        cache_set = AsyncMock()

        with patch.dict("utils.kurler._CLIENTS", {"deezer": client}, clear=True), patch(
            "utils.kurler.cache.get", new=AsyncMock(return_value=None)
        ), patch("utils.kurler.cache.set", new=cache_set):
            result = await _search_by_identifier(
                "deezer", "GBX1234", search="search_by_isrc", url_getter="extract_track_url", via="isrc"
            )

        assert result is None
        cache_set.assert_not_awaited()
