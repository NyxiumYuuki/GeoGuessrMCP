"""
Integration tests for authentication flow.

These tests verify the complete authentication workflow including
login, session management, and token validation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from geoguessr_mcp.auth.session import SessionManager, UserSession


class TestAuthenticationFlow:
    """Integration tests for authentication flow with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_complete_login_flow(self, session_manager, mock_httpx_client, mock_profile_data):
        """Test complete login flow from credentials to session."""
        # Setup mock responses
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []
        login_response.headers = {"set-cookie": "_ncfa=test_cookie_value; Path=/; HttpOnly"}

        mock_cookie = MagicMock()
        mock_cookie.name = "_ncfa"
        mock_cookie.value = "test_cookie_value"
        login_response.cookies.jar.append(mock_cookie)

        profile_response = MagicMock()
        profile_response.status_code = 200
        profile_response.json.return_value = mock_profile_data

        mock_httpx_client.post = AsyncMock(return_value=login_response)
        mock_httpx_client.get = AsyncMock(return_value=profile_response)
        mock_httpx_client.cookies.set = MagicMock()

        # Perform login
        session_token, session = await session_manager.login("user@example.com", "password123")

        # Verify session was created
        assert session_token is not None
        assert len(session_token) > 20  # Token should be significant
        assert session.ncfa_cookie == "test_cookie_value"
        assert session.username == "TestPlayer"
        assert session.user_id == "test-user-id"
        assert session.is_valid()

        # Verify session can be retrieved
        retrieved_session = await session_manager.get_session(session_token)
        assert retrieved_session is not None
        assert retrieved_session.username == session.username

    @pytest.mark.asyncio
    async def test_login_then_logout(self, session_manager, mock_httpx_client, mock_profile_data):
        """Test login followed by logout invalidates session."""
        # Setup login mocks
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []
        mock_cookie = MagicMock()
        mock_cookie.name = "_ncfa"
        mock_cookie.value = "test_cookie"
        login_response.cookies.jar.append(mock_cookie)

        profile_response = MagicMock()
        profile_response.status_code = 200
        profile_response.json.return_value = mock_profile_data

        mock_httpx_client.post = AsyncMock(return_value=login_response)
        mock_httpx_client.get = AsyncMock(return_value=profile_response)
        mock_httpx_client.cookies.set = MagicMock()

        # Login
        session_token, _ = await session_manager.login("user@example.com", "password")

        # Verify session exists
        session_before = await session_manager.get_session(session_token)
        assert session_before is not None

        # Logout
        logout_result = await session_manager.logout(session_token)
        assert logout_result is True

        # Verify session is invalidated
        session_after = await session_manager.get_session(session_token)
        assert session_after is None

    @pytest.mark.asyncio
    async def test_multiple_user_sessions(self, session_manager, mock_httpx_client):
        """Test managing multiple user sessions."""
        # Setup responses for two different users
        user1_profile = {"id": "user1", "nick": "User1", "email": "user1@example.com"}
        user2_profile = {"id": "user2", "nick": "User2", "email": "user2@example.com"}

        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []
        mock_cookie = MagicMock()
        mock_cookie.name = "_ncfa"
        mock_cookie.value = "cookie_value"
        login_response.cookies.jar.append(mock_cookie)

        profile_response1 = MagicMock()
        profile_response1.status_code = 200
        profile_response1.json.return_value = user1_profile

        profile_response2 = MagicMock()
        profile_response2.status_code = 200
        profile_response2.json.return_value = user2_profile

        mock_httpx_client.post = AsyncMock(return_value=login_response)
        mock_httpx_client.cookies.set = MagicMock()

        # Login user 1
        mock_httpx_client.get = AsyncMock(return_value=profile_response1)
        token1, session1 = await session_manager.login("user1@example.com", "pass1")

        # Login user 2
        mock_httpx_client.get = AsyncMock(return_value=profile_response2)
        token2, session2 = await session_manager.login("user2@example.com", "pass2")

        # Both sessions should be valid
        assert token1 != token2
        assert (await session_manager.get_session(token1)) is not None
        assert (await session_manager.get_session(token2)) is not None

    @pytest.mark.asyncio
    async def test_session_replacement_same_user(
            self, session_manager, mock_httpx_client, mock_profile_data
    ):
        """Test that logging in as same user replaces old session."""
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []
        mock_cookie = MagicMock()
        mock_cookie.name = "_ncfa"
        mock_cookie.value = "cookie_value"
        login_response.cookies.jar.append(mock_cookie)

        profile_response = MagicMock()
        profile_response.status_code = 200
        profile_response.json.return_value = mock_profile_data

        mock_httpx_client.post = AsyncMock(return_value=login_response)
        mock_httpx_client.get = AsyncMock(return_value=profile_response)
        mock_httpx_client.cookies.set = MagicMock()

        # First login
        token1, _ = await session_manager.login("user@example.com", "pass")

        # Second login as same user
        token2, _ = await session_manager.login("user@example.com", "pass")

        # First token should be invalid, second should be valid
        assert token1 != token2
        assert (await session_manager.get_session(token1)) is None
        assert (await session_manager.get_session(token2)) is not None

    @pytest.mark.asyncio
    async def test_expired_session_cleanup(self, session_manager):
        """Test that expired sessions are cleaned up when accessed."""
        # Manually create an expired session
        expired_session = UserSession(
            ncfa_cookie="expired_cookie",
            user_id="expired_user",
            username="ExpiredUser",
            email="expired@example.com",
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired yesterday
        )

        # Store the expired session
        async with session_manager._lock:
            session_manager._sessions["expired_token"] = expired_session
            session_manager._user_sessions["expired_user"] = "expired_token"

        # Try to get the session - should return None and clean up
        session = await session_manager.get_session("expired_token")
        assert session is None

        # Verify cleanup
        assert "expired_token" not in session_manager._sessions
        assert "expired_user" not in session_manager._user_sessions

    @pytest.mark.asyncio
    async def test_default_cookie_fallback(self, session_manager):
        """Test falling back to default cookie when no session exists."""
        # Create manager with default cookie
        manager_with_default = SessionManager(default_cookie="default_test_cookie")

        # Get session without logging in - should return default
        session = await manager_with_default.get_session()

        assert session is not None
        assert session.ncfa_cookie == "default_test_cookie"
        assert session.user_id == "default"

    @pytest.mark.asyncio
    async def test_set_default_cookie(self, session_manager):
        """Test setting default cookie after initialization."""
        # Initially no default
        session = await session_manager.get_session()
        assert session is None

        # Set default cookie
        await session_manager.set_default_cookie("new_default_cookie")

        # Now should return default session
        session = await session_manager.get_session()
        assert session is not None
        assert session.ncfa_cookie == "new_default_cookie"


class TestLoginErrorHandling:
    """Tests for login error scenarios."""

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, session_manager, mock_httpx_client):
        """Test login with invalid credentials."""
        response = MagicMock()
        response.status_code = 401
        mock_httpx_client.post = AsyncMock(return_value=response)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await session_manager.login("wrong@example.com", "wrong_password")

    @pytest.mark.asyncio
    async def test_login_account_denied(self, session_manager, mock_httpx_client):
        """Test login when account access is denied."""
        response = MagicMock()
        response.status_code = 403
        mock_httpx_client.post = AsyncMock(return_value=response)

        with pytest.raises(ValueError, match="Account access denied"):
            await session_manager.login("banned@example.com", "password")

    @pytest.mark.asyncio
    async def test_login_rate_limited(self, session_manager, mock_httpx_client):
        """Test login when rate limited."""
        response = MagicMock()
        response.status_code = 429
        mock_httpx_client.post = AsyncMock(return_value=response)

        with pytest.raises(ValueError, match="Too many login attempts"):
            await session_manager.login("user@example.com", "password")

    @pytest.mark.asyncio
    async def test_login_server_error(self, session_manager, mock_httpx_client):
        """Test login with server error."""
        response = MagicMock()
        response.status_code = 500
        mock_httpx_client.post = AsyncMock(return_value=response)

        with pytest.raises(ValueError, match="Login failed: 500"):
            await session_manager.login("user@example.com", "password")

    @pytest.mark.asyncio
    async def test_login_no_cookie_received(self, session_manager, mock_httpx_client):
        """Test login when no cookie is received."""
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []  # No cookies
        login_response.headers = {}  # No set-cookie header

        mock_httpx_client.post = AsyncMock(return_value=login_response)

        with pytest.raises(ValueError, match="No session cookie received"):
            await session_manager.login("user@example.com", "password")

    @pytest.mark.asyncio
    async def test_login_profile_fetch_fails(self, session_manager, mock_httpx_client):
        """Test login when profile fetch fails after successful auth."""
        # Login succeeds
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.cookies.jar = []
        mock_cookie = MagicMock()
        mock_cookie.name = "_ncfa"
        mock_cookie.value = "valid_cookie"
        login_response.cookies.jar.append(mock_cookie)

        # Profile fetch fails
        profile_response = MagicMock()
        profile_response.status_code = 500

        mock_httpx_client.post = AsyncMock(return_value=login_response)
        mock_httpx_client.get = AsyncMock(return_value=profile_response)
        mock_httpx_client.cookies.set = MagicMock()

        with pytest.raises(ValueError, match="Failed to retrieve user profile"):
            await session_manager.login("user@example.com", "password")


class TestCookieValidation:
    """Tests for cookie validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_valid_cookie(self, session_manager, mock_profile_data):
        """Test validating a valid cookie."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_profile_data
            mock_client.get = AsyncMock(return_value=response)
            mock_client.cookies.set = MagicMock()

            result = await session_manager.validate_cookie("valid_cookie")

            assert result is not None
            assert result["id"] == "test-user-id"
            assert result["nick"] == "TestPlayer"

    @pytest.mark.asyncio
    async def test_validate_invalid_cookie(self, session_manager):
        """Test validating an invalid cookie."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = MagicMock()
            response.status_code = 401
            mock_client.get = AsyncMock(return_value=response)
            mock_client.cookies.set = MagicMock()

            result = await session_manager.validate_cookie("invalid_cookie")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_cookie_network_error(self, session_manager):
        """Test cookie validation with network error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Network error"))
            mock_client.cookies.set = MagicMock()

            result = await session_manager.validate_cookie("cookie")

            assert result is None


@pytest.mark.integration
class TestRealAuthFlow:
    """
    Real integration tests requiring actual GeoGuessr credentials.

    These tests are skipped unless GEOGUESSR_NCFA_COOKIE is set and
    running with -m integration flag.
    """

    @pytest.mark.asyncio
    async def test_real_cookie_validation(self, session_manager):
        """Test validating a real cookie against the API."""
        import os

        cookie = os.environ.get("GEOGUESSR_NCFA_COOKIE")
        if not cookie:
            pytest.skip("GEOGUESSR_NCFA_COOKIE not set")

        result = await session_manager.validate_cookie(cookie)

        assert result is not None
        assert "id" in result
        assert "nick" in result
