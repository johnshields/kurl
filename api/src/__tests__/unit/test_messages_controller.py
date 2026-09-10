"""
Tests for api.controllers.messages_controller -- send, list threads, read a
thread, delete a message.
"""

import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from api.controllers import messages_controller


def _fetch_one_router(**rows):
    """Route fetch_one by which query string was passed. Keys: thread_by_uid,
    thread_by_pair, user_by_uid, user_by_username, are_friends, message_by_uid."""

    async def _stub(db, sql, *params):
        if "FROM threads WHERE uid" in sql:
            return rows.get("thread_by_uid")
        if "user_a_uid = ? AND user_b_uid" in sql:
            return rows.get("thread_by_pair")
        if "FROM users WHERE uid" in sql:
            return rows.get("user_by_uid")
        if "WHERE username" in sql:
            return rows.get("user_by_username")
        if "SELECT 1 FROM friends" in sql:
            return rows.get("are_friends")
        if "FROM messages WHERE uid" in sql:
            return rows.get("message_by_uid")
        return None

    return _stub


def _fetch_all_router(messages=None, threads=None):
    async def _stub(db, sql, *params):
        if "FROM threads t" in sql:
            return threads or []
        return messages or []

    return _stub


def _thread_row(uid="THR_1", a="USR_X", b="USR_Y"):
    return {
        "uid": uid,
        "user_a_uid": a,
        "user_b_uid": b,
        "last_message_at": "2026-01-01T00:00:00.000Z",
        "last_read_a_at": None,
        "last_read_b_at": None,
        "created_at": "2026-01-01T00:00:00.000Z",
    }


def _msg_row(uid="MSG_1", body="hi", kurl=None):
    return {
        "uid": uid,
        "thread_uid": "THR_1",
        "sender_uid": "USR_X",
        "body": body,
        "kurl": kurl,
        "kurl_recipient": None,
        "created_at": "2026-01-01T00:00:00.000Z",
    }


def _summary_row(uid="THR_1"):
    return {
        "uid": uid,
        "last_message_at": "2026-01-01T00:00:00.000Z",
        "created_at": "2026-01-01T00:00:00.000Z",
        "other_uid": "USR_Y",
        "other_username": "cool-cat",
        "last_body": "yo",
        "last_kurl": None,
        "last_sender_uid": "USR_Y",
        "last_at": "2026-01-01T00:00:00.000Z",
        "unread": 2,
    }


class TestSend:
    async def test_rejects_empty_message(self):
        result = await messages_controller.send(db=object(), user_uid="USR_X", data={})
        assert result["code"] == "EMPTY_MESSAGE"

    async def test_rejects_overlong_body(self):
        result = await messages_controller.send(
            db=object(), user_uid="USR_X", data={"body": "x" * 2001}
        )
        assert result["code"] == "BODY_TOO_LONG"

    async def test_rejects_non_object_kurl(self):
        result = await messages_controller.send(
            db=object(), user_uid="USR_X", data={"kurl": "not-an-object"}
        )
        assert result["code"] == "INVALID_REQUEST"

    async def test_unknown_recipient_is_not_found(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_username=None),
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"toUsername": "ghost", "body": "hi"}
            )
        assert result["code"] == "NOT_FOUND"

    async def test_cannot_message_self(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_X"}),
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"toUid": "USR_X", "body": "hi"}
            )
        assert result["code"] == "INVALID_REQUEST"

    async def test_requires_an_accepted_friendship(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(
                user_by_username={"uid": "USR_Y"}, thread_by_pair=None, are_friends=None
            ),
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"toUsername": "cool-cat", "body": "hi"}
            )
        assert result["code"] == "NOT_FRIENDS"

    async def test_thread_uid_must_belong_to_the_caller(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(thread_by_uid=_thread_row(a="USR_P", b="USR_Q")),
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"threadUid": "THR_1", "body": "hi"}
            )
        assert result["code"] == "NOT_FOUND"

    async def test_creates_thread_and_message_for_a_new_recipient(self):
        execute_mock = AsyncMock()
        router = _fetch_one_router(
            user_by_username={"uid": "USR_Y"},
            thread_by_pair=None,
            are_friends=1,
            thread_by_uid=_thread_row(),
            message_by_uid=_msg_row(body="hi"),
        )
        with patch("api.controllers.messages_controller.fetch_one", router), patch(
            "api.controllers.messages_controller.execute", execute_mock
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"toUsername": "cool-cat", "body": "hi"}
            )
        assert result["status"] == "success"
        assert result["data"]["uid"] == "MSG_1"
        assert result["data"]["body"] == "hi"
        # thread INSERT, message INSERT, thread TOUCH, mark-read
        assert execute_mock.await_count == 4

    async def test_sends_into_an_existing_thread(self):
        execute_mock = AsyncMock()
        router = _fetch_one_router(
            thread_by_uid=_thread_row(),
            are_friends=1,
            message_by_uid=_msg_row(body="yo"),
        )
        with patch("api.controllers.messages_controller.fetch_one", router), patch(
            "api.controllers.messages_controller.execute", execute_mock
        ):
            result = await messages_controller.send(
                db=object(), user_uid="USR_X", data={"threadUid": "THR_1", "body": "yo"}
            )
        assert result["status"] == "success"
        # message INSERT, thread TOUCH, mark-read -- no thread INSERT
        assert execute_mock.await_count == 3

    async def test_attached_kurl_is_json_encoded_on_insert(self):
        execute_mock = AsyncMock()
        router = _fetch_one_router(
            thread_by_uid=_thread_row(),
            are_friends=1,
            message_by_uid=_msg_row(body=None, kurl='{"resolved_url": "https://x"}'),
        )
        with patch("api.controllers.messages_controller.fetch_one", router), patch(
            "api.controllers.messages_controller.execute", execute_mock
        ):
            result = await messages_controller.send(
                db=object(),
                user_uid="USR_X",
                data={"threadUid": "THR_1", "kurl": {"resolved_url": "https://x"}},
            )
        assert result["status"] == "success"
        # execute(db, sql, uid, thread_uid, sender_uid, body, kurl_json, kurl_recipient)
        insert_args = execute_mock.await_args_list[0].args
        assert insert_args[5] is None
        assert insert_args[6] == '{"resolved_url": "https://x"}'
        assert insert_args[7] is None
        assert result["data"]["kurl"] == {"resolved_url": "https://x"}

    async def test_stores_the_recipient_reresolve_on_the_message(self):
        execute_mock = AsyncMock()
        router = _fetch_one_router(
            thread_by_uid=_thread_row(),
            are_friends=1,
            user_by_uid={"uid": "USR_Y", "preferred_platform": "tidal"},
            message_by_uid=_msg_row(body=None, kurl='{"source_url": "https://s"}'),
        )
        fake = SimpleNamespace(
            resolve=AsyncMock(
                return_value={"resolved_url": "https://tidal/x", "platform": "tidal", "via": "isrc"}
            )
        )
        with patch("api.controllers.messages_controller.fetch_one", router), patch(
            "api.controllers.messages_controller.execute", execute_mock
        ), patch.dict(sys.modules, {"api.services.urls": fake}):
            result = await messages_controller.send(
                db=object(),
                user_uid="USR_X",
                data={"threadUid": "THR_1", "kurl": {"source_url": "https://s", "platform": "spotify"}},
            )
        assert result["status"] == "success"
        insert_args = execute_mock.await_args_list[0].args
        assert json.loads(insert_args[7]) == {
            "target_url": "https://tidal/x",
            "platform": "tidal",
            "via": "isrc",
        }


class TestResolveForRecipient:
    async def test_none_without_a_source_url(self):
        got = await messages_controller._resolve_for_recipient(
            object(), "USR_Y", {"platform": "spotify"}
        )
        assert got is None

    async def test_none_when_recipient_has_no_preference(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "preferred_platform": None}),
        ):
            got = await messages_controller._resolve_for_recipient(
                object(), "USR_Y", {"source_url": "https://s", "platform": "spotify"}
            )
        assert got is None

    async def test_none_when_preference_matches_attached_platform(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "preferred_platform": "spotify"}),
        ):
            got = await messages_controller._resolve_for_recipient(
                object(), "USR_Y", {"source_url": "https://s", "platform": "spotify"}
            )
        assert got is None

    async def test_reresolves_into_the_preferred_platform(self):
        fake = SimpleNamespace(
            resolve=AsyncMock(
                return_value={"resolved_url": "https://tidal/x", "platform": "tidal", "via": "isrc"}
            )
        )
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "preferred_platform": "tidal"}),
        ), patch.dict(sys.modules, {"api.services.urls": fake}):
            got = await messages_controller._resolve_for_recipient(
                object(), "USR_Y", {"source_url": "https://s", "platform": "spotify"}
            )
        assert got == {"target_url": "https://tidal/x", "platform": "tidal", "via": "isrc"}
        fake.resolve.assert_awaited_once()

    async def test_none_when_resolve_raises(self):
        fake = SimpleNamespace(resolve=AsyncMock(side_effect=RuntimeError("odesli down")))
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "preferred_platform": "tidal"}),
        ), patch.dict(sys.modules, {"api.services.urls": fake}):
            got = await messages_controller._resolve_for_recipient(
                object(), "USR_Y", {"source_url": "https://s", "platform": "spotify"}
            )
        assert got is None


class TestNotifyRecipient:
    async def test_skips_when_opted_out(self):
        send_mock = AsyncMock()
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "email": "y@b.com", "notify_email": 0}),
        ), patch("api.controllers.messages_controller.email_client.send", send_mock):
            await messages_controller._notify_recipient(object(), "USR_Y", "USR_X", "hi", None)
        send_mock.assert_not_awaited()

    async def test_skips_when_recipient_has_no_email(self):
        send_mock = AsyncMock()
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(user_by_uid={"uid": "USR_Y", "email": None, "notify_email": 1}),
        ), patch("api.controllers.messages_controller.email_client.send", send_mock):
            await messages_controller._notify_recipient(object(), "USR_Y", "USR_X", "hi", None)
        send_mock.assert_not_awaited()

    async def test_sends_when_opted_in(self):
        send_mock = AsyncMock()
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(
                user_by_uid={
                    "uid": "USR_Y",
                    "email": "y@b.com",
                    "username": "cool-cat",
                    "notify_email": 1,
                }
            ),
        ), patch("api.controllers.messages_controller.email_client.send", send_mock):
            await messages_controller._notify_recipient(object(), "USR_Y", "USR_X", "hey there", None)
        send_mock.assert_awaited_once()
        kwargs = send_mock.await_args.kwargs
        assert kwargs["to"] == "y@b.com"
        assert "cool-cat" in kwargs["subject"]

    async def test_never_raises_on_failure(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            AsyncMock(side_effect=RuntimeError("d1 down")),
        ):
            await messages_controller._notify_recipient(object(), "USR_Y", "USR_X", "hi", None)


class TestGetThread:
    async def test_missing_thread_is_not_found(self):
        with patch(
            "api.controllers.messages_controller.fetch_one", _fetch_one_router(thread_by_uid=None)
        ):
            result = await messages_controller.get_thread(
                db=object(), user_uid="USR_X", thread_uid="THR_1"
            )
        assert result["code"] == "NOT_FOUND"

    async def test_non_participant_is_not_found(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(thread_by_uid=_thread_row(a="USR_P", b="USR_Q")),
        ):
            result = await messages_controller.get_thread(
                db=object(), user_uid="USR_X", thread_uid="THR_1"
            )
        assert result["code"] == "NOT_FOUND"

    async def test_returns_header_and_messages_and_marks_read(self):
        execute_mock = AsyncMock()
        router = _fetch_one_router(
            thread_by_uid=_thread_row(), user_by_uid={"uid": "USR_Y", "username": "cool-cat"}
        )
        with patch("api.controllers.messages_controller.fetch_one", router), patch(
            "api.controllers.messages_controller.fetch_all",
            _fetch_all_router(messages=[_msg_row(), _msg_row(uid="MSG_2")]),
        ), patch("api.controllers.messages_controller.execute", execute_mock):
            result = await messages_controller.get_thread(
                db=object(), user_uid="USR_X", thread_uid="THR_1"
            )
        assert result["status"] == "success"
        assert result["data"]["thread"]["user"] == {"uid": "USR_Y", "username": "cool-cat"}
        assert [m["uid"] for m in result["data"]["messages"]] == ["MSG_1", "MSG_2"]
        execute_mock.assert_awaited_once()


class TestMarkRead:
    async def test_non_participant_is_not_found(self):
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(thread_by_uid=_thread_row(a="USR_P", b="USR_Q")),
        ):
            result = await messages_controller.mark_read(
                db=object(), user_uid="USR_X", thread_uid="THR_1"
            )
        assert result["code"] == "NOT_FOUND"

    async def test_marks_the_callers_side(self):
        execute_mock = AsyncMock()
        with patch(
            "api.controllers.messages_controller.fetch_one",
            _fetch_one_router(thread_by_uid=_thread_row(a="USR_X", b="USR_Y")),
        ), patch("api.controllers.messages_controller.execute", execute_mock):
            result = await messages_controller.mark_read(
                db=object(), user_uid="USR_X", thread_uid="THR_1"
            )
        assert result["status"] == "success"
        assert "last_read_a_at" in execute_mock.await_args.args[1]


class TestDeleteMessage:
    async def test_deletes_scoped_to_sender(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.messages_controller.execute", execute_mock):
            result = await messages_controller.delete_message(
                db=object(), user_uid="USR_X", message_uid="MSG_1"
            )
        assert result["status"] == "success"
        assert execute_mock.await_args.args[-2:] == ("MSG_1", "USR_X")


class TestListThreads:
    async def test_maps_summary_rows(self):
        with patch(
            "api.controllers.messages_controller.fetch_all",
            _fetch_all_router(threads=[_summary_row(), _summary_row(uid="THR_2")]),
        ):
            result = await messages_controller.list_threads(db=object(), user_uid="USR_X")
        assert [t["uid"] for t in result["data"]] == ["THR_1", "THR_2"]
        assert result["data"][0]["unread"] == 2
        assert result["data"][0]["lastMessage"]["body"] == "yo"
