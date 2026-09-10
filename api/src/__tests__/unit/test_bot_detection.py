"""
Tests for utils.bot_detection -- crawler / headless-client user agents.
"""

from utils.bot_detection import is_bot


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
            assert is_bot(ua) is True, ua

    def test_real_browser_user_agents_pass(self):
        browser_uas = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]
        for ua in browser_uas:
            assert is_bot(ua) is False, ua

    def test_missing_user_agent_is_treated_as_bot(self):
        assert is_bot("") is True
        assert is_bot(None) is True

    def test_match_is_case_insensitive(self):
        assert is_bot("GOOGLEBOT/2.1") is True
