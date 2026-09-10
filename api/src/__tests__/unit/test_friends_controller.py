"""
Tests for api.controllers.friends_controller -- send, accept, list, remove
on the friend-request graph.
"""

from unittest.mock import AsyncMock, patch

from api.controllers import friends_controller


def _fetch_one_stub(username_row=None, between_row=None, friend_row=None):
    """Route fetch_one's mocked calls by which query string was passed."""

    async def _stub(db, sql, *params):
        if "WHERE username" in sql:
            return username_row
        if "OR (requester_uid" in sql:
            return between_row
        if "FROM friends WHERE uid" in sql:
            return friend_row
        return None

    return _stub


def _fetch_all_stub(accepted=None, incoming=None, outgoing=None):
    async def _stub(db, sql, *params):
        if "status = 'accepted' AND (f.requester_uid" in sql:
            return accepted or []
        if "u.uid = f.requester_uid" in sql:
            return incoming or []
        if "u.uid = f.addressee_uid" in sql:
            return outgoing or []
        return []

    return _stub


def _row(uid="FRN_1", other="USR_Y", name="cool-cat", status="accepted"):
    return {
        "uid": uid,
        "status": status,
        "created_at": "2026-01-01T00:00:00.000Z",
        "responded_at": "2026-01-02T00:00:00.000Z",
        "other_uid": other,
        "other_username": name,
    }


class TestSendRequest:
    async def test_rejects_empty_username(self):
        result = await friends_controller.send_request(db=object(), user_uid="USR_X", data={})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_REQUEST"

    async def test_rejects_unknown_username(self):
        with patch("api.controllers.friends_controller.fetch_one", _fetch_one_stub(username_row=None)):
            result = await friends_controller.send_request(
                db=object(), user_uid="USR_X", data={"username": "ghost"}
            )
        assert result["code"] == "NOT_FOUND"

    async def test_rejects_self(self):
        with patch(
            "api.controllers.friends_controller.fetch_one",
            _fetch_one_stub(username_row={"uid": "USR_X"}),
        ):
            result = await friends_controller.send_request(
                db=object(), user_uid="USR_X", data={"username": "me"}
            )
        assert result["code"] == "INVALID_REQUEST"

    async def test_rejects_when_already_friends(self):
        with patch(
            "api.controllers.friends_controller.fetch_one",
            _fetch_one_stub(username_row={"uid": "USR_Y"}, between_row={"status": "accepted"}),
        ):
            result = await friends_controller.send_request(
                db=object(), user_uid="USR_X", data={"username": "cool-cat"}
            )
        assert result["code"] == "ALREADY_FRIENDS"

    async def test_rejects_when_a_request_is_pending(self):
        with patch(
            "api.controllers.friends_controller.fetch_one",
            _fetch_one_stub(username_row={"uid": "USR_Y"}, between_row={"status": "pending"}),
        ):
            result = await friends_controller.send_request(
                db=object(), user_uid="USR_X", data={"username": "cool-cat"}
            )
        assert result["code"] == "REQUEST_EXISTS"

    async def test_creates_a_pending_request(self):
        execute_mock = AsyncMock()
        with patch(
            "api.controllers.friends_controller.fetch_one",
            _fetch_one_stub(username_row={"uid": "USR_Y"}, between_row=None),
        ), patch("api.controllers.friends_controller.execute", execute_mock):
            result = await friends_controller.send_request(
                db=object(), user_uid="USR_X", data={"username": "cool-cat"}
            )
        assert result["status"] == "success"
        assert result["data"]["uid"].startswith("FRN_")
        execute_mock.assert_awaited_once()
        args = execute_mock.await_args.args
        assert args[-2:] == ("USR_X", "USR_Y")


class TestAcceptRequest:
    async def test_missing_request_is_not_found(self):
        with patch("api.controllers.friends_controller.fetch_one", _fetch_one_stub(friend_row=None)):
            result = await friends_controller.accept_request(db=object(), user_uid="USR_X", friend_uid="FRN_1")
        assert result["code"] == "NOT_FOUND"

    async def test_only_the_addressee_can_accept(self):
        row = {"addressee_uid": "USR_OTHER", "status": "pending"}
        with patch("api.controllers.friends_controller.fetch_one", _fetch_one_stub(friend_row=row)):
            result = await friends_controller.accept_request(db=object(), user_uid="USR_X", friend_uid="FRN_1")
        assert result["code"] == "NOT_FOUND"

    async def test_already_accepted_is_not_found(self):
        row = {"addressee_uid": "USR_X", "status": "accepted"}
        with patch("api.controllers.friends_controller.fetch_one", _fetch_one_stub(friend_row=row)):
            result = await friends_controller.accept_request(db=object(), user_uid="USR_X", friend_uid="FRN_1")
        assert result["code"] == "NOT_FOUND"

    async def test_accepts_a_pending_request(self):
        execute_mock = AsyncMock()
        row = {"addressee_uid": "USR_X", "status": "pending"}
        with patch("api.controllers.friends_controller.fetch_one", _fetch_one_stub(friend_row=row)), patch(
            "api.controllers.friends_controller.execute", execute_mock
        ):
            result = await friends_controller.accept_request(db=object(), user_uid="USR_X", friend_uid="FRN_1")
        assert result["status"] == "success"
        execute_mock.assert_awaited_once()
        assert execute_mock.await_args.args[-2:] == ("FRN_1", "USR_X")


class TestRemove:
    async def test_deletes_scoped_to_a_participant(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.friends_controller.execute", execute_mock):
            result = await friends_controller.remove(db=object(), user_uid="USR_X", friend_uid="FRN_1")
        assert result["status"] == "success"
        execute_mock.assert_awaited_once()
        assert execute_mock.await_args.args[-3:] == ("FRN_1", "USR_X", "USR_X")


class TestListFriends:
    async def test_buckets_rows_into_friends_incoming_outgoing(self):
        stub = _fetch_all_stub(
            accepted=[_row(uid="FRN_A", status="accepted")],
            incoming=[_row(uid="FRN_B", status="pending")],
            outgoing=[_row(uid="FRN_C", status="pending")],
        )
        with patch("api.controllers.friends_controller.fetch_all", stub):
            result = await friends_controller.list_friends(db=object(), user_uid="USR_X")

        data = result["data"]
        assert [f["uid"] for f in data["friends"]] == ["FRN_A"]
        assert [f["uid"] for f in data["incoming"]] == ["FRN_B"]
        assert [f["uid"] for f in data["outgoing"]] == ["FRN_C"]
        assert data["friends"][0]["user"] == {"uid": "USR_Y", "username": "cool-cat"}

    async def test_empty_when_no_rows(self):
        with patch("api.controllers.friends_controller.fetch_all", _fetch_all_stub()):
            result = await friends_controller.list_friends(db=object(), user_uid="USR_X")
        assert result["data"] == {"friends": [], "incoming": [], "outgoing": []}
