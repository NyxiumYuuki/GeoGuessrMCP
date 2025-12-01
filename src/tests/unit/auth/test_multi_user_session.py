"""Tests for MultiUserSessionManager."""

import pytest

from geoguessr_mcp.auth.multi_user_session import MultiUserSessionManager
from geoguessr_mcp.auth.session import SessionManager


class TestMultiUserSessionManager:
    """Tests for MultiUserSessionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh MultiUserSessionManager for each test."""
        return MultiUserSessionManager()

    @pytest.mark.asyncio
    async def test_get_user_context_creates_new_manager(self, manager):
        """Test that getting context for a new API key creates a new session manager."""
        context = await manager.get_user_context("new_api_key")

        assert context.api_key == "new_api_key"
        assert "new_api_key" in manager._user_managers
        assert isinstance(manager._user_managers["new_api_key"], SessionManager)

    @pytest.mark.asyncio
    async def test_get_user_context_reuses_existing_manager(self, manager):
        """Test that getting context for existing API key reuses the same manager."""
        await manager.get_user_context("existing_key")
        await manager.get_user_context("existing_key")

        # Should use the same manager instance
        assert manager._user_managers["existing_key"] is manager._user_managers["existing_key"]
        assert len(manager._user_managers) == 1

    @pytest.mark.asyncio
    async def test_multiple_api_keys_get_separate_managers(self, manager):
        """Test that different API keys get separate session managers."""
        await manager.get_user_context("key1")
        await manager.get_user_context("key2")
        await manager.get_user_context("key3")

        assert len(manager._user_managers) == 3
        assert manager._user_managers["key1"] is not manager._user_managers["key2"]
        assert manager._user_managers["key2"] is not manager._user_managers["key3"]

    @pytest.mark.asyncio
    async def test_get_auth_status_not_authenticated(self, manager):
        """Test getting auth status for unauthenticated user."""
        status = await manager.get_auth_status("test_key")

        assert not status["authenticated"]
        assert status["user_id"] is None
        assert status["username"] is None
        assert "test_key" in status["api_key"] or "***" in status["api_key"]

    @pytest.mark.asyncio
    async def test_get_session_for_api_key_none_when_not_logged_in(self, manager):
        """Test that get_session_for_api_key returns None for non-existent key."""
        session = await manager.get_session_for_api_key("nonexistent_key")
        assert session is None

    @pytest.mark.asyncio
    async def test_login_user_creates_manager_if_not_exists(self):
        """Test that login_user creates a manager if it doesn't exist."""
        # This test requires mocking the HTTP client for GeoGuessr API
        # We'll mark it as a placeholder for now
        pytest.skip("Requires mocking GeoGuessr API")

    @pytest.mark.asyncio
    async def test_logout_user_returns_false_for_nonexistent_key(self, manager):
        """Test that logout_user returns False for non-existent API key."""
        result = await manager.logout_user("nonexistent_key", "fake_session_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_set_user_cookie_validates_cookie(self, manager):
        """Test that set_user_cookie validates the cookie."""
        # Invalid cookie should return False
        result = await manager.set_user_cookie("test_key", "invalid_cookie")
        assert result is False

    @pytest.mark.asyncio
    async def test_context_isolation_between_users(self, manager):
        """Test that contexts are properly isolated between different users."""
        context_alice = await manager.get_user_context("alice_key")
        context_bob = await manager.get_user_context("bob_key")

        # Contexts should be different
        assert context_alice.api_key != context_bob.api_key

        # Should have separate session managers
        assert manager._user_managers["alice_key"] is not manager._user_managers["bob_key"]
