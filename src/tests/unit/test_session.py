"""Unit tests for session management."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geoguessr_mcp.auth.session import SessionManager, UserSession

# ============================================================================
# USER SESSION TESTS
# ============================================================================


class TestUserSession:
    """Tests for UserSession dataclass."""

    def test_valid_session(self):
        """Test that a valid session is recognized as valid."""
        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="TestUser",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        assert session.is_valid()

    def test_expired_session(self):
        """Test that an expired session is invalid."""
        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="TestUser",
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        assert not session.is_valid()

    def test_session_without_cookie(self):
        """Test that a session without cookie is invalid."""
        session = UserSession(
            ncfa_cookie="", user_id="user123", username="TestUser", email="test@example.com"
        )
        assert not session.is_valid()


# ============================================================================
# SESSION MANAGER TESTS
# ============================================================================

class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_profile_response):
        """Test successful login flow."""

        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create mock client
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock login response
            login_response = MagicMock()
            login_response.status_code = 200
            login_response.cookies.jar = []

            # Create mock cookie
            mock_cookie = MagicMock()
            mock_cookie.name = "_ncfa"
            mock_cookie.value = "test_ncfa_cookie_value"
            login_response.cookies.jar.append(mock_cookie)

            # Mock profile response
            profile_response = MagicMock()
            profile_response.status_code = 200
            profile_response.json.return_value = mock_profile_response

            # Set up mock client responses
            mock_client.post = AsyncMock(return_value=login_response)
            mock_client.get = AsyncMock(return_value=profile_response)
            mock_client.cookies.set = MagicMock()

            # Perform login
            session_token, session = await manager.login("test@example.com", "password123")

            # Assertions
            assert session_token is not None
            assert len(session_token) > 0
            assert session.ncfa_cookie == "test_ncfa_cookie_value"
            assert session.user_id == "test-user-id"
            assert session.username == "TestPlayer"
            assert session.email == "test@example.com"
            assert session.is_valid()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock 401 response
            login_response = MagicMock()
            login_response.status_code = 401
            mock_client.post = AsyncMock(return_value=login_response)

            # Attempt login and expect error
            with pytest.raises(ValueError, match="Invalid email or password"):
                await manager.login("wrong@example.com", "wrong_pass")

    @pytest.mark.asyncio
    async def test_logout(self, mock_profile_response):
        """Test logout functionality."""

        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
            # Set up successful login first
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            login_response = MagicMock()
            login_response.status_code = 200
            login_response.cookies.jar = []
            mock_cookie = MagicMock()
            mock_cookie.name = "_ncfa"
            mock_cookie.value = "test_cookie"
            login_response.cookies.jar.append(mock_cookie)

            profile_response = MagicMock()
            profile_response.status_code = 200
            profile_response.json.return_value = mock_profile_response

            mock_client.post = AsyncMock(return_value=login_response)
            mock_client.get = AsyncMock(return_value=profile_response)
            mock_client.cookies.set = MagicMock()

            session_token, _ = await manager.login("test@example.com", "password")

            # Now logout
            result = await manager.logout(session_token)
            assert result is True

            # Verify session is removed
            session = await manager.get_session(session_token)
            assert session is None

    @pytest.mark.asyncio
    async def test_get_session_with_default_cookie(self):
        """Test getting session with default cookie from environment."""

        manager = SessionManager()

        # Should use default cookie from environment
        session = await manager.get_session()
        assert session is not None
        assert session.ncfa_cookie == "test_cookie_value"
