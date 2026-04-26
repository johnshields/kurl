"""
Integration tests for POST /api/kurl -- exercises the full request pipeline
with cache disabled and platform clients mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Build a TestClient with cache disabled (no lifespan context)."""
    # Import inside fixture so env-var stubs in conftest apply first.
    from entry import app

    # Disable cache side effects.
    with (
        patch("clients.cache.get", new=AsyncMock(return_value=None)),
        patch("clients.cache.set", new=AsyncMock(return_value=None)),
    ):
        yield TestClient(app)


@pytest.fixture
def mock_platform_clients():
    """Swap out the kurler's _CLIENTS registry with mocks for the endpoint tests."""
    clients = {}
    for name in ("spotify", "appleMusic", "deezer", "tidal"):
        m = MagicMock()
        m.is_configured.return_value = True
        clients[name] = m
    with patch.dict("utils.kurler._CLIENTS", clients, clear=True):
        yield clients


class TestKurlEndpoint:
    def test_missing_target_platform_returns_400(self, client):
        r = client.post("/api/kurl", json={"url": "https://open.spotify.com/track/abc"})
        assert r.status_code == 422  # pydantic rejects missing field

    def test_unknown_platform_returns_400(self, client):
        r = client.post(
            "/api/kurl",
            json={"url": "https://open.spotify.com/track/abc", "target_platform": "napster"},
        )
        assert r.status_code == 400
        assert "Unknown platform" in r.json()["detail"]

    def test_search_url_returns_400(self, client):
        r = client.post(
            "/api/kurl",
            json={"url": "https://open.spotify.com/search/foo", "target_platform": "deezer"},
        )
        assert r.status_code == 400
        assert "search url" in r.json()["detail"].lower()

    def test_isrc_happy_path(self, client, mock_platform_clients):
        """Spotify track -> Deezer via ISRC returns a direct link."""
        mock_platform_clients["spotify"].get_track = AsyncMock(return_value={"external_ids": {"isrc": "GB123"}})
        mock_platform_clients["spotify"].extract_isrc.return_value = "GB123"
        mock_platform_clients["spotify"].extract_metadata.return_value = ("Hello", "Adele")

        mock_platform_clients["deezer"].search_by_isrc = AsyncMock(
            return_value={"link": "https://deezer.com/track/999"}
        )
        mock_platform_clients["deezer"].extract_track_url.return_value = "https://deezer.com/track/999"
        mock_platform_clients["deezer"].extract_metadata.return_value = ("Hello", "Adele")

        r = client.post(
            "/api/kurl",
            json={
                "url": "https://open.spotify.com/track/6QJVQSuMC77psM4vgPo31D",
                "target_platform": "deezer",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        assert body["data"]["resolved_url"] == "https://deezer.com/track/999"
        assert body["data"]["via"] == "isrc"
        assert body["data"]["platform"] == "deezer"

    def test_falls_back_to_odesli_when_kurler_returns_none(self, client, mock_platform_clients):
        """When target platform has no client, kurler returns None and Odesli takes over."""
        odesli_response = {
            "linksByPlatform": {
                "amazonMusic": {"url": "https://music.amazon.com/albums/X?trackAsin=Y"},
            },
            "entitiesByUniqueId": {"x": {"title": "Song", "artistName": "Artist"}},
        }
        with patch("clients.odesli.resolve_by_id", new=AsyncMock(return_value=odesli_response)):
            r = client.post(
                "/api/kurl",
                json={
                    "url": "https://open.spotify.com/track/abc",
                    "target_platform": "amazonMusic",
                },
            )

        assert r.status_code == 200
        body = r.json()
        assert body["data"]["resolved_url"].startswith("https://music.amazon.com")
        assert body["data"]["via"] == "direct"

    def test_search_url_fallback_when_all_else_fails(self, client, mock_platform_clients):
        """Odesli returns no target link -> build search URL from metadata."""
        odesli_response = {
            "linksByPlatform": {"youtube": {"url": "https://youtube.com/watch?v=x"}},
            "entitiesByUniqueId": {"x": {"title": "Song", "artistName": "Artist"}},
        }
        with patch("clients.odesli.resolve_by_id", new=AsyncMock(return_value=odesli_response)):
            # Prevent the kurler from succeeding by making target search fail.
            mock_platform_clients["deezer"].search_by_isrc = AsyncMock(return_value=None)
            mock_platform_clients["deezer"].search_track = AsyncMock(return_value=None)
            mock_platform_clients["spotify"].get_track = AsyncMock(return_value={})
            mock_platform_clients["spotify"].extract_isrc.return_value = None
            mock_platform_clients["spotify"].extract_metadata.return_value = (None, None)

            with patch("clients.metadata.fetch_metadata", new=AsyncMock(return_value=(None, None))):
                r = client.post(
                    "/api/kurl",
                    json={
                        "url": "https://open.spotify.com/track/abc",
                        "target_platform": "amazonMusic",
                    },
                )

        assert r.status_code == 200
        body = r.json()
        assert body["data"]["via"] == "search"
        assert "amazon.com/search" in body["data"]["resolved_url"]
