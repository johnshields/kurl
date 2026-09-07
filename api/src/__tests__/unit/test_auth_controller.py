"""
Tests for api.controllers.auth_controller -- signup, login, profile updates.
"""

from unittest.mock import AsyncMock, patch

from api.controllers import auth_controller


def _fetch_one_stub(by_email=None, by_username=None, by_uid=None):
    """Route fetch_one's mocked calls by which query string was passed."""

    async def _stub(db, sql, *params):
        if "WHERE email" in sql:
            return by_email
        if "WHERE username" in sql:
            return by_username
        if "WHERE uid" in sql:
            return by_uid
        return None

    return _stub


class TestSignup:
    async def test_rejects_invalid_email(self):
        result = await auth_controller.signup(db=object(), data={"email": "not-an-email", "password": "longenough"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_EMAIL"

    async def test_rejects_short_password(self):
        result = await auth_controller.signup(db=object(), data={"email": "a@b.com", "password": "short"})
        assert result["status"] == "error"
        assert result["code"] == "WEAK_PASSWORD"

    async def test_rejects_taken_email(self):
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email={"uid": "USR_X"})):
            result = await auth_controller.signup(
                db=object(), data={"email": "taken@b.com", "password": "longenough"}
            )
        assert result["status"] == "error"
        assert result["code"] == "EMAIL_TAKEN"

    async def test_creates_account_with_generated_username(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", _fetch_one_stub()
        ), patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.signup(db=object(), data={"email": "new@b.com", "password": "longenough"})

        assert result["status"] == "success"
        assert result["data"]["user"]["email"] == "new@b.com"
        assert result["data"]["user"]["username"]
        assert result["data"]["token"]
        execute_mock.assert_awaited_once()


class TestLogin:
    async def test_unknown_email_fails(self):
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email=None)):
            result = await auth_controller.login(db=object(), data={"email": "ghost@b.com", "password": "whatever"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_CREDENTIALS"

    async def test_wrong_password_fails(self):
        from utils.password import hash_password

        row = {"uid": "USR_X", "password_hash": hash_password("correct-password")}
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email=row)):
            result = await auth_controller.login(db=object(), data={"email": "a@b.com", "password": "wrong"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_CREDENTIALS"

    async def test_correct_credentials_succeed(self):
        from utils.password import hash_password

        row = {
            "uid": "USR_X",
            "email": "a@b.com",
            "username": "cool-name",
            "password_hash": hash_password("correct-password"),
            "preferred_platform": None,
            "created_at": "2026-01-01T00:00:00.000Z",
        }
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email=row)), patch(
            "api.controllers.auth_controller.settings"
        ) as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.login(db=object(), data={"email": "a@b.com", "password": "correct-password"})

        assert result["status"] == "success"
        assert result["data"]["user"]["uid"] == "USR_X"
        assert result["data"]["token"]


class TestUpdateProfile:
    async def test_rejects_invalid_username(self):
        result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"username": "ab"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_USERNAME"

    async def test_rejects_username_taken_by_someone_else(self):
        with patch(
            "api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_username={"uid": "USR_OTHER"})
        ):
            result = await auth_controller.update_profile(
                db=object(), user_uid="USR_X", data={"username": "taken-name"}
            )
        assert result["status"] == "error"
        assert result["code"] == "USERNAME_TAKEN"

    async def test_allows_keeping_own_username(self):
        execute_mock = AsyncMock()
        stub = _fetch_one_stub(
            by_username={"uid": "USR_X"},
            by_uid={
                "uid": "USR_X",
                "email": "a@b.com",
                "username": "my-name",
                "preferred_platform": None,
                "created_at": "2026-01-01T00:00:00.000Z",
            },
        )
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", stub
        ):
            result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"username": "my-name"})
        assert result["status"] == "success"

    async def test_rejects_unknown_platform(self):
        result = await auth_controller.update_profile(
            db=object(), user_uid="USR_X", data={"preferredPlatform": "not-a-real-platform"}
        )
        assert result["status"] == "error"
        assert result["code"] == "UNKNOWN_PLATFORM"

    async def test_updates_preferred_platform(self):
        execute_mock = AsyncMock()
        stub = _fetch_one_stub(
            by_uid={
                "uid": "USR_X",
                "email": "a@b.com",
                "username": "my-name",
                "preferred_platform": "spotify",
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        )
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", stub
        ):
            result = await auth_controller.update_profile(
                db=object(), user_uid="USR_X", data={"preferredPlatform": "spotify"}
            )
        assert result["status"] == "success"
        assert result["data"]["preferredPlatform"] == "spotify"

    async def test_clears_preferred_platform_when_none(self):
        execute_mock = AsyncMock()
        stub = _fetch_one_stub(
            by_uid={
                "uid": "USR_X",
                "email": "a@b.com",
                "username": "my-name",
                "preferred_platform": None,
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        )
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", stub
        ):
            result = await auth_controller.update_profile(
                db=object(), user_uid="USR_X", data={"preferredPlatform": None}
            )
        assert result["status"] == "success"
        assert result["data"]["preferredPlatform"] is None
        assert execute_mock.await_args.args[-2:] == (None, "USR_X")

    async def test_rejects_short_password(self):
        result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"password": "short"})
        assert result["status"] == "error"
        assert result["code"] == "WEAK_PASSWORD"

    async def test_updates_password(self):
        execute_mock = AsyncMock()
        stub = _fetch_one_stub(
            by_uid={
                "uid": "USR_X",
                "email": "a@b.com",
                "username": "my-name",
                "preferred_platform": None,
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        )
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", stub
        ):
            result = await auth_controller.update_profile(
                db=object(), user_uid="USR_X", data={"password": "longenough"}
            )
        assert result["status"] == "success"
        execute_mock.assert_awaited_once()

    async def test_rejects_invalid_email(self):
        result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"email": "not-an-email"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_EMAIL"

    async def test_rejects_when_email_already_set(self):
        stub = _fetch_one_stub(by_uid={"uid": "USR_X", "email": "already@set.com"})
        with patch("api.controllers.auth_controller.fetch_one", stub):
            result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"email": "new@b.com"})
        assert result["status"] == "error"
        assert result["code"] == "EMAIL_ALREADY_SET"

    async def test_rejects_email_taken_by_someone_else(self):
        stub = _fetch_one_stub(by_uid={"uid": "USR_X", "email": None}, by_email={"uid": "USR_OTHER"})
        with patch("api.controllers.auth_controller.fetch_one", stub):
            result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"email": "taken@b.com"})
        assert result["status"] == "error"
        assert result["code"] == "EMAIL_TAKEN"

    async def test_adds_email_and_sends_verification(self):
        execute_mock = AsyncMock()
        send_mock = AsyncMock()
        stub = _fetch_one_stub(
            by_uid={
                "uid": "USR_X",
                "email": None,
                "username": "my-name",
                "preferred_platform": None,
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        )
        with patch("api.controllers.auth_controller.execute", execute_mock), patch(
            "api.controllers.auth_controller.fetch_one", stub
        ), patch("api.controllers.auth_controller.email_client.send", send_mock), patch(
            "api.controllers.auth_controller.settings"
        ) as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.update_profile(db=object(), user_uid="USR_X", data={"email": "new@b.com"})
        assert result["status"] == "success"
        execute_mock.assert_awaited_once()
        send_mock.assert_awaited_once()


class TestForgotPassword:
    async def test_always_succeeds_even_for_unknown_email(self):
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email=None)):
            result = await auth_controller.forgot_password(db=object(), data={"email": "ghost@b.com"})
        assert result["status"] == "success"

    async def test_sends_an_email_when_the_account_exists(self):
        row = {"uid": "USR_X", "password_hash": "some-hash"}
        send_mock = AsyncMock(return_value=True)
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_email=row)), patch(
            "api.controllers.auth_controller.email_client.send", send_mock
        ), patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.forgot_password(db=object(), data={"email": "a@b.com"})
        assert result["status"] == "success"
        send_mock.assert_awaited_once()
        assert send_mock.await_args.kwargs["to"] == "a@b.com"


class TestResetPassword:
    async def test_rejects_short_password(self):
        result = await auth_controller.reset_password(db=object(), data={"token": "x", "password": "short"})
        assert result["status"] == "error"
        assert result["code"] == "WEAK_PASSWORD"

    async def test_rejects_invalid_token(self):
        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.reset_password(
                db=object(), data={"token": "garbage", "password": "longenough"}
            )
        assert result["status"] == "error"
        assert result["code"] == "INVALID_TOKEN"

    async def test_rejects_a_stale_token_after_password_already_changed(self):
        from utils.password_reset import create_reset_token

        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_reset_token("USR_X", "old-hash", "test-secret")

            row = {"uid": "USR_X", "password_hash": "new-hash"}
            with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)):
                result = await auth_controller.reset_password(
                    db=object(), data={"token": token, "password": "longenough"}
                )
        assert result["status"] == "error"
        assert result["code"] == "INVALID_TOKEN"

    async def test_resets_password_and_returns_a_session(self):
        from utils.password_reset import create_reset_token

        execute_mock = AsyncMock()
        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_reset_token("USR_X", "old-hash", "test-secret")

            row = {
                "uid": "USR_X",
                "email": "a@b.com",
                "username": "my-name",
                "password_hash": "old-hash",
                "preferred_platform": None,
                "created_at": "2026-01-01T00:00:00.000Z",
            }
            with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)), patch(
                "api.controllers.auth_controller.execute", execute_mock
            ):
                result = await auth_controller.reset_password(
                    db=object(), data={"token": token, "password": "longenough"}
                )
        assert result["status"] == "success"
        assert result["data"]["token"]
        assert result["data"]["user"]["uid"] == "USR_X"
        execute_mock.assert_awaited_once()


class TestVerifyEmail:
    async def test_rejects_invalid_token(self):
        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.verify_email(db=object(), data={"token": "garbage"})
        assert result["status"] == "error"
        assert result["code"] == "INVALID_TOKEN"

    async def test_rejects_unknown_account(self):
        from utils.email_verification import create_verification_token

        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_verification_token("USR_X", "test-secret")
            with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=None)):
                result = await auth_controller.verify_email(db=object(), data={"token": token})
        assert result["status"] == "error"
        assert result["code"] == "NOT_FOUND"

    async def test_marks_the_account_verified(self):
        from utils.email_verification import create_verification_token

        execute_mock = AsyncMock()
        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_verification_token("USR_X", "test-secret")
            row = {"uid": "USR_X", "email_verified_at": None}
            with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)), patch(
                "api.controllers.auth_controller.execute", execute_mock
            ):
                result = await auth_controller.verify_email(db=object(), data={"token": token})
        assert result["status"] == "success"
        execute_mock.assert_awaited_once()

    async def test_is_idempotent_when_already_verified(self):
        from utils.email_verification import create_verification_token

        execute_mock = AsyncMock()
        with patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            token = create_verification_token("USR_X", "test-secret")
            row = {"uid": "USR_X", "email_verified_at": "2026-01-01T00:00:00.000Z"}
            with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)), patch(
                "api.controllers.auth_controller.execute", execute_mock
            ):
                result = await auth_controller.verify_email(db=object(), data={"token": token})
        assert result["status"] == "success"
        execute_mock.assert_not_awaited()


class TestResendVerification:
    async def test_rejects_unknown_account(self):
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=None)):
            result = await auth_controller.resend_verification(db=object(), user_uid="USR_X")
        assert result["status"] == "error"
        assert result["code"] == "NOT_FOUND"

    async def test_short_circuits_when_already_verified(self):
        row = {"uid": "USR_X", "email": "a@b.com", "email_verified_at": "2026-01-01T00:00:00.000Z"}
        send_mock = AsyncMock()
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)), patch(
            "api.controllers.auth_controller.email_client.send", send_mock
        ):
            result = await auth_controller.resend_verification(db=object(), user_uid="USR_X")
        assert result["status"] == "success"
        send_mock.assert_not_awaited()

    async def test_resends_when_unverified(self):
        row = {"uid": "USR_X", "email": "a@b.com", "email_verified_at": None}
        send_mock = AsyncMock(return_value=True)
        with patch("api.controllers.auth_controller.fetch_one", _fetch_one_stub(by_uid=row)), patch(
            "api.controllers.auth_controller.email_client.send", send_mock
        ), patch("api.controllers.auth_controller.settings") as mock_settings:
            mock_settings.SESSION_SECRET = "test-secret"
            result = await auth_controller.resend_verification(db=object(), user_uid="USR_X")
        assert result["status"] == "success"
        send_mock.assert_awaited_once()
        assert send_mock.await_args.kwargs["to"] == "a@b.com"
