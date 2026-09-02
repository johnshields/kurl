"""
Tests for api.controllers.events_controller -- bot filtering and event writes.
"""

from unittest.mock import AsyncMock, patch

from api.controllers import events_controller


class TestIsBot:
    def test_known_bot_user_agents_are_flagged(self):
        bot_uas = [
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "facebookexternalhit/1.1",
            "AhrefsBot/7.0",
            "Mozilla/5.0 SemrushBot/7~bl",
            "Mozilla/5.0 HeadlessChrome/120.0.0.0 Safari/537.36",
            "Slurp",
            "DuckDuckBot/1.1",
        ]
        for ua in bot_uas:
            assert events_controller._is_bot(ua) is True, ua

    def test_real_browser_user_agents_pass(self):
        browser_uas = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]
        for ua in browser_uas:
            assert events_controller._is_bot(ua) is False, ua

    def test_missing_user_agent_is_treated_as_bot(self):
        assert events_controller._is_bot("") is True
        assert events_controller._is_bot(None) is True

    def test_match_is_case_insensitive(self):
        assert events_controller._is_bot("GOOGLEBOT/2.1") is True


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
