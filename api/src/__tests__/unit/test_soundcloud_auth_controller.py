"""
Tests for api.controllers.oauth.soundcloud_auth_controller -- Sign in with
SoundCloud, both anonymous (find-or-create) and linked (an existing
session) modes.
"""

from unittest.mock import AsyncMock, patch

from api.controllers.oauth import soundcloud_auth_controller
from utils.oauth_state import create_oauth_state


def _configured_settings(mock_settings):
    mock_settings.SOUNDCLOUD_CLIENT_ID = "client-id"
    mock_settings.SOUNDCLOUD_CLIENT_SECRET = "client-secret"
    mock_settings.SOUNDCLOUD_REDIRECT_URI = "https://api.kurl.online/api/auth/soundcloud/callback"
    mock_settings.SOUNDCLOUD_APP_REDIRECT_URL = "https://kurl.online/settings"
    mock_settings.SESSION_SECRET = "test-secret"


def _fetch_one_stub(by_soundcloud_user_id=None):
    async def _stub(db, sql, *params):
        if "soundcloud_user_id" in sql:
            return by_soundcloud_user_id
        return None

    return _stub


class TestIsConfigured:
    def test_false_when_redirect_uri_missing(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            mock_settings.SOUNDCLOUD_CLIENT_ID = "client-id"
            mock_settings.SOUNDCLOUD_CLIENT_SECRET = "client-secret"
            mock_settings.SOUNDCLOUD_REDIRECT_URI = None
            assert soundcloud_auth_controller.is_configured() is False

    def test_true_when_all_present(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            assert soundcloud_auth_controller.is_configured() is True


class TestBuildAuthorizeUrl:
    def test_returns_none_when_not_configured(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            mock_settings.SOUNDCLOUD_CLIENT_ID = None
            mock_settings.SOUNDCLOUD_CLIENT_SECRET = None
            mock_settings.SOUNDCLOUD_REDIRECT_URI = None
            assert soundcloud_auth_controller.build_authorize_url(None) is None

    def test_returns_url_with_pkce_challenge_when_anonymous(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = soundcloud_auth_controller.build_authorize_url(None)
        assert url is not None
        assert url.startswith("https://secure.soundcloud.com/authorize?")
        assert "client_id=client-id" in url
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert "state=" in url

    def test_returns_url_when_linking_an_existing_session(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = soundcloud_auth_controller.build_authorize_url("USR_X")
        assert url is not None
        assert "state=" in url


class TestHandleCallback:
    async def test_redirects_with_error_when_code_or_state_missing(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await soundcloud_auth_controller.handle_callback(db=object(), code=None, state=None, error=None)
        assert url == "https://kurl.online/settings?soundcloud=error"

    async def test_redirects_with_error_when_soundcloud_reports_one(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await soundcloud_auth_controller.handle_callback(
                db=object(), code=None, state=None, error="access_denied"
            )
        assert url == "https://kurl.online/settings?soundcloud=error"

    async def test_redirects_with_error_when_state_invalid(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await soundcloud_auth_controller.handle_callback(
                db=object(), code="a-code", state="garbage", error=None
            )
        assert url == "https://kurl.online/settings?soundcloud=error"

    async def test_redirects_with_error_when_state_has_no_pkce_verifier(self):
        """A state token created without a verifier (shouldn't happen from
        build_authorize_url, but the callback must not silently proceed)."""
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret")
            url = await soundcloud_auth_controller.handle_callback(
                db=object(), code="a-code", state=state, error=None
            )
        assert url == "https://kurl.online/settings?soundcloud=error"

    async def test_redirects_with_error_when_token_exchange_fails(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret", verifier="verifier-abc")
            with patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.exchange_code",
                AsyncMock(side_effect=RuntimeError("soundcloud unavailable")),
            ):
                url = await soundcloud_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url == "https://kurl.online/settings?soundcloud=error"

    async def test_links_to_existing_session_when_state_carries_a_subject(self):
        """Linked mode -- the state came from an already-signed-in session,
        so the callback must use that user_uid rather than resolving one."""
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret", user_uid="USR_LINKED", verifier="verifier-abc")
            with patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": 12345, "username": "jane"}),
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await soundcloud_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        # Already had a session -- no new token minted or handed back.
        assert url == "https://kurl.online/settings?soundcloud=connected"
        execute_mock.assert_awaited_once()
        args = execute_mock.await_args.args
        assert args[-7] == "USR_LINKED"

    async def test_signs_in_to_an_existing_account_already_linked_by_soundcloud_id(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret", verifier="verifier-abc")
            with patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": 12345, "username": "jane"}),
            ), patch(
                "api.controllers.oauth.oauth_signin.fetch_one",
                _fetch_one_stub(by_soundcloud_user_id={"user_uid": "USR_EXISTING"}),
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await soundcloud_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url.startswith("https://kurl.online/settings?soundcloud=connected&token=")
        args = execute_mock.await_args.args
        assert args[-7] == "USR_EXISTING"

    async def test_creates_a_new_account_when_no_match_found(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret", verifier="verifier-abc")
            with patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.soundcloud_auth_controller.soundcloud_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": 12345, "username": "jane"}),
            ), patch(
                "api.controllers.oauth.oauth_signin.fetch_one", _fetch_one_stub()
            ), patch(
                "api.controllers.oauth.oauth_signin.unique_username", AsyncMock(return_value="brave-otter")
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await soundcloud_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url.startswith("https://kurl.online/settings?soundcloud=connected&token=")
        # First execute call creates the user row (no email), second upserts the SoundCloud link.
        assert execute_mock.await_count == 2
        create_user_args = execute_mock.await_args_list[0].args
        assert create_user_args[-3:] == (None, "brave-otter", None)


class TestGetLinkedAccount:
    async def test_returns_connected_false_when_not_linked(self):
        with patch("api.controllers.oauth.oauth_signin.fetch_one", AsyncMock(return_value=None)):
            result = await soundcloud_auth_controller.get_linked_account(db=object(), user_uid="USR_X")
        assert result == {"connected": False}

    async def test_returns_identity_when_linked(self):
        row = {"soundcloud_user_id": "12345", "display_name": "jane"}
        with patch("api.controllers.oauth.oauth_signin.fetch_one", AsyncMock(return_value=row)):
            result = await soundcloud_auth_controller.get_linked_account(db=object(), user_uid="USR_X")
        assert result == {"connected": True, "soundcloudUserId": "12345", "displayName": "jane"}


class TestDisconnect:
    async def test_deletes_the_linked_account(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
            await soundcloud_auth_controller.disconnect(db=object(), user_uid="USR_X")
        execute_mock.assert_awaited_once()
