"""
Tests for api.controllers.kurls_controller -- recording and listing a
signed-in user's saved kurl history.
"""

from unittest.mock import AsyncMock, patch

from api.controllers import kurls_controller


class TestRecordKurl:
    async def test_records_a_kurl(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.kurls_controller.execute", execute_mock):
            await kurls_controller.record_kurl(
                db=object(),
                user_uid="USR_X",
                source_url="https://open.spotify.com/track/abc",
                target_url="https://music.apple.com/us/song/_/1",
                platform="appleMusic",
                via="isrc",
                title="Hello",
                artist="Adele",
            )
        execute_mock.assert_awaited_once()

    async def test_never_raises_when_the_write_fails(self):
        """Recording is best-effort -- must never break the caller's flow."""
        execute_mock = AsyncMock(side_effect=RuntimeError("d1 unavailable"))
        with patch("api.controllers.kurls_controller.execute", execute_mock):
            await kurls_controller.record_kurl(
                db=object(),
                user_uid="USR_X",
                source_url="https://open.spotify.com/track/abc",
                target_url="https://music.apple.com/us/song/_/1",
                platform="appleMusic",
                via="isrc",
                title="Hello",
                artist="Adele",
            )
        execute_mock.assert_awaited_once()


class TestListKurls:
    async def test_returns_mapped_rows(self):
        rows = [
            {
                "uid": "KRL_1",
                "source_url": "https://open.spotify.com/track/abc",
                "target_url": "https://music.apple.com/us/song/_/1",
                "platform": "appleMusic",
                "via": "isrc",
                "title": "Hello",
                "artist": "Adele",
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        ]
        with patch("api.controllers.kurls_controller.fetch_all", AsyncMock(return_value=rows)):
            result = await kurls_controller.list_kurls(db=object(), user_uid="USR_X")

        assert result["status"] == "success"
        assert result["data"][0]["uid"] == "KRL_1"
        assert result["data"][0]["sourceUrl"] == "https://open.spotify.com/track/abc"

    async def test_returns_empty_list_when_no_history(self):
        with patch("api.controllers.kurls_controller.fetch_all", AsyncMock(return_value=[])):
            result = await kurls_controller.list_kurls(db=object(), user_uid="USR_X")
        assert result["data"] == []


class TestDeleteKurl:
    async def test_deletes_scoped_to_owner(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.kurls_controller.execute", execute_mock):
            result = await kurls_controller.delete_kurl(db=object(), user_uid="USR_X", kurl_uid="KRL_1")

        execute_mock.assert_awaited_once()
        args = execute_mock.await_args.args
        assert args[-2:] == ("KRL_1", "USR_X")
        assert result["status"] == "success"
