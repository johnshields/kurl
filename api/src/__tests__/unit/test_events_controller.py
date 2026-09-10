"""
Tests for api.controllers.events_controller -- bot filtering and event writes.
"""

from unittest.mock import AsyncMock, patch

from api.controllers import events_controller


class TestCreateEvent:
    async def test_bot_request_is_ignored_without_db_write(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.events_controller.execute", execute_mock):
            result = await events_controller.create_event(
                db=object(),
                data={"type": "page_view"},
                meta={"userAgent": "Googlebot/2.1"},
            )

        execute_mock.assert_not_awaited()
        assert result == {"status": "success", "message": "Ignored.", "uid": None}

    async def test_missing_user_agent_request_is_ignored(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.events_controller.execute", execute_mock):
            result = await events_controller.create_event(
                db=object(),
                data={"type": "page_view"},
                meta={},
            )

        execute_mock.assert_not_awaited()
        assert result["uid"] is None

    async def test_real_request_is_recorded(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.events_controller.execute", execute_mock):
            result = await events_controller.create_event(
                db=object(),
                data={
                    "type": "kurl",
                    "sourceUrl": "https://open.spotify.com/track/x",
                    "platform": "deezer",
                },
                meta={"userAgent": "Mozilla/5.0 (Macintosh) Chrome/120.0.0.0", "country": "GB"},
            )

        execute_mock.assert_awaited_once()
        assert result["status"] == "success"
        assert result["uid"] is not None
        assert result["uid"].startswith("EVT_")
