"""
This module contains test cases for the UserSession dataclass and the
SessionManager class, which handle session authentication and management
functionality.

The test cases validate the implementation of session validity, login,
logout, and retrieval features for these classes under various scenarios.
These tests ensure that the session and authentication-related operations
perform correctly and as expected under different conditions.

Classes
-------
TestUserSession
    Provides unit tests for the UserSession dataclass, which represents
    user session details.

TestSessionManager
    Provides unit tests for the SessionManager class, which facilitates
    login, logout, and session management operations in an async context.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from geoguessr_mcp.auth.session import SessionManager, UserSession


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
            ncfa_cookie="",
            user_id="user123",
            username="TestUser",
            email="test@example.com",
        )
        assert not session.is_valid()

    def test_session_no_expiry(self):
        """Test session without expiration date."""
        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="TestUser",
            email="test@example.com",
            expires_at=None,
        )
        assert session.is_valid()


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_profile_response):
        """Test successful login flow."""
        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock login response
            login_response = MagicMock()
            login_response.status_code = 200
            login_response.cookies.jar = []

            mock_cookie = MagicMock()
            mock_cookie.name = "_ncfa"
            mock_cookie.value = "test_ncfa_cookie_value"
            login_response.cookies.jar.append(mock_cookie)

            # Mock profile response
            profile_response = MagicMock()
            profile_response.status_code = 200
            profile_response.json.return_value = mock_profile_response

            mock_client.post = AsyncMock(return_value=login_response)
            mock_client.get = AsyncMock(return_value=profile_response)
            mock_client.cookies.set = MagicMock()

            # Perform login
            session_token, session = await manager.login("test@example.com", "password123")

            assert session_token is not None
            assert len(session_token) > 0
            assert session.ncfa_cookie == "test_ncfa_cookie_value"
            assert session.user_id == "test-user-id-123"
            assert session.username == "TestPlayer"
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

            login_response = MagicMock()
            login_response.status_code = 401
            mock_client.post = AsyncMock(return_value=login_response)

            with pytest.raises(ValueError, match="Invalid email or password"):
                await manager.login("wrong@example.com", "wrong_pass")

    @pytest.mark.asyncio
    async def test_login_rate_limited(self):
        """Test login when rate limited."""
        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            login_response = MagicMock()
            login_response.status_code = 429
            mock_client.post = AsyncMock(return_value=login_response)

            with pytest.raises(ValueError, match="Too many login attempts"):
                await manager.login("test@example.com", "password")

    @pytest.mark.asyncio
    async def test_logout(self, mock_profile_response):
        """Test logout functionality."""
        manager = SessionManager()

        with patch("httpx.AsyncClient") as mock_client_class:
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

            # Logout
            result = await manager.logout(session_token)
            assert result is True

            # Verify session is removed
            session = await manager.get_session(session_token)
            assert session is None

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        manager = SessionManager()
        result = await manager.logout("invalid_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_with_default_cookie(self):
        """Test getting session with default cookie."""
        manager = SessionManager(default_cookie="default_test_cookie")

        session = await manager.get_session()

        assert session is not None
        assert session.ncfa_cookie == "default_test_cookie"
        assert session.user_id == "default"

    @pytest.mark.asyncio
    async def test_get_session_no_auth(self):
        """Test getting session with no authentication."""
        manager = SessionManager(default_cookie=None)

        session = await manager.get_session()
        assert session is None

    @pytest.mark.asyncio
    async def test_set_default_cookie(self):
        """Test setting default cookie."""
        manager = SessionManager()

        await manager.set_default_cookie("new_cookie")

        session = await manager.get_session()
        assert session is not None
        assert session.ncfa_cookie == "new_cookie"
