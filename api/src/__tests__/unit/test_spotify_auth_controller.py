"""
Tests for api.controllers.oauth.spotify_auth_controller -- Sign in with Spotify,
both anonymous (find-or-create) and linked (an existing session) modes.
"""

from unittest.mock import AsyncMock, patch

from api.controllers.oauth import spotify_auth_controller
from utils.auth.oauth_state import create_oauth_state


def _configured_settings(mock_settings):
    mock_settings.SPOTIFY_CLIENT_ID = "client-id"
    mock_settings.SPOTIFY_CLIENT_SECRET = "client-secret"
    mock_settings.SPOTIFY_REDIRECT_URI = "https://api.kurl.online/api/auth/spotify/callback"
    mock_settings.SPOTIFY_APP_REDIRECT_URL = "https://kurl.online/settings"
    mock_settings.SESSION_SECRET = "test-secret"


def _fetch_one_stub(by_spotify_user_id=None, by_email=None):
    async def _stub(db, sql, *params):
        if "spotify_user_id" in sql:
            return by_spotify_user_id
        if "WHERE email" in sql:
            return by_email
        return None

    return _stub


class TestIsConfigured:
    def test_false_when_redirect_uri_missing(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = "client-id"
            mock_settings.SPOTIFY_CLIENT_SECRET = "client-secret"
            mock_settings.SPOTIFY_REDIRECT_URI = None
            assert spotify_auth_controller.is_configured() is False

    def test_true_when_all_present(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            assert spotify_auth_controller.is_configured() is True


class TestBuildAuthorizeUrl:
    def test_returns_none_when_not_configured(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = None
            mock_settings.SPOTIFY_CLIENT_SECRET = None
            mock_settings.SPOTIFY_REDIRECT_URI = None
            assert spotify_auth_controller.build_authorize_url(None) is None

    def test_returns_url_without_state_subject_when_anonymous(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = spotify_auth_controller.build_authorize_url(None)
        assert url is not None
        assert url.startswith("https://accounts.spotify.com/authorize?")
        assert "client_id=client-id" in url
        assert "state=" in url

    def test_returns_url_when_linking_an_existing_session(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = spotify_auth_controller.build_authorize_url("USR_X")
        assert url is not None
        assert "state=" in url


class TestHandleCallback:
    async def test_redirects_with_error_when_code_or_state_missing(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await spotify_auth_controller.handle_callback(db=object(), code=None, state=None, error=None)
        assert url == "https://kurl.online/settings?spotify=error"

    async def test_redirects_with_error_when_spotify_reports_one(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await spotify_auth_controller.handle_callback(
                db=object(), code=None, state=None, error="access_denied"
            )
        assert url == "https://kurl.online/settings?spotify=error"

    async def test_redirects_with_error_when_state_invalid(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            url = await spotify_auth_controller.handle_callback(
                db=object(), code="a-code", state="garbage", error=None
            )
        assert url == "https://kurl.online/settings?spotify=error"

    async def test_redirects_with_error_when_token_exchange_fails(self):
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret")
            with patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.exchange_code",
                AsyncMock(side_effect=RuntimeError("spotify unavailable")),
            ):
                url = await spotify_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url == "https://kurl.online/settings?spotify=error"

    async def test_links_to_existing_session_when_state_carries_a_subject(self):
        """Linked mode -- the state came from an already-signed-in session,
        so the callback must use that user_uid rather than resolving one."""
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret", user_uid="USR_LINKED")
            with patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": "spotify_uid", "display_name": "Jane"}),
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await spotify_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        # Already had a session -- no new token minted or handed back.
        assert url == "https://kurl.online/settings?spotify=connected"
        execute_mock.assert_awaited_once()
        args = execute_mock.await_args.args
        assert args[-7] == "USR_LINKED"

    async def test_signs_in_to_an_existing_account_already_linked_by_spotify_id(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret")
            with patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": "spotify_uid", "display_name": "Jane"}),
            ), patch(
                "api.controllers.oauth.oauth_signin.fetch_one",
                _fetch_one_stub(by_spotify_user_id={"user_uid": "USR_EXISTING"}),
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await spotify_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url.startswith("https://kurl.online/settings?spotify=connected&token=")
        args = execute_mock.await_args.args
        assert args[-7] == "USR_EXISTING"

    async def test_signs_in_to_an_existing_account_matched_by_email(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret")
            with patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": "spotify_uid", "display_name": "Jane", "email": "jane@b.com"}),
            ), patch(
                "api.controllers.oauth.oauth_signin.fetch_one",
                _fetch_one_stub(by_email={"uid": "USR_BY_EMAIL"}),
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await spotify_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url.startswith("https://kurl.online/settings?spotify=connected&token=")
        args = execute_mock.await_args.args
        assert args[-7] == "USR_BY_EMAIL"

    async def test_creates_a_new_account_when_no_match_found(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.settings") as mock_settings:
            _configured_settings(mock_settings)
            state = create_oauth_state("test-secret")
            with patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.exchange_code",
                AsyncMock(return_value={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}),
            ), patch(
                "api.controllers.oauth.spotify_auth_controller.spotify_oauth_client.fetch_profile",
                AsyncMock(return_value={"id": "spotify_uid", "display_name": "Jane", "email": "jane@b.com"}),
            ), patch(
                "api.controllers.oauth.oauth_signin.fetch_one", _fetch_one_stub()
            ), patch(
                "api.controllers.oauth.oauth_signin.unique_username", AsyncMock(return_value="brave-otter")
            ), patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
                url = await spotify_auth_controller.handle_callback(
                    db=object(), code="a-code", state=state, error=None
                )
        assert url.startswith("https://kurl.online/settings?spotify=connected&token=")
        # First execute call creates the user row, second upserts the Spotify link.
        assert execute_mock.await_count == 2
        create_user_args = execute_mock.await_args_list[0].args
        assert create_user_args[-3:] == ("jane@b.com", "brave-otter", None)


class TestGetLinkedAccount:
    async def test_returns_connected_false_when_not_linked(self):
        with patch("api.controllers.oauth.oauth_signin.fetch_one", AsyncMock(return_value=None)):
            result = await spotify_auth_controller.get_linked_account(db=object(), user_uid="USR_X")
        assert result == {"connected": False}

    async def test_returns_identity_when_linked(self):
        row = {"spotify_user_id": "spotify_uid", "display_name": "Jane"}
        with patch("api.controllers.oauth.oauth_signin.fetch_one", AsyncMock(return_value=row)):
            result = await spotify_auth_controller.get_linked_account(db=object(), user_uid="USR_X")
        assert result == {"connected": True, "spotifyUserId": "spotify_uid", "displayName": "Jane"}


class TestDisconnect:
    async def test_deletes_the_linked_account(self):
        execute_mock = AsyncMock()
        with patch("api.controllers.oauth.oauth_signin.execute", execute_mock):
            await spotify_auth_controller.disconnect(db=object(), user_uid="USR_X")
        execute_mock.assert_awaited_once()
