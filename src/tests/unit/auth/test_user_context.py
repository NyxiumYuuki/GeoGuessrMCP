"""Tests for UserContext class."""

import pytest

from geoguessr_mcp.auth.session import UserSession
from geoguessr_mcp.auth.user_context import UserContext
from datetime import datetime, timedelta, UTC


class TestUserContext:
    """Tests for UserContext class."""

    def test_user_context_without_session(self):
        """Test user context without a GeoGuessr session."""
        context = UserContext(api_key="test_key_123")

        assert context.api_key == "test_key_123"
        assert context.session is None
        assert not context.is_authenticated
        assert context.ncfa_cookie is None
        assert "anonymous_" in context.user_id
        assert "User-" in context.username

    def test_user_context_with_session(self):
        """Test user context with a GeoGuessr session."""
        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="testuser",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        context = UserContext(api_key="test_key_123", session=session)

        assert context.api_key == "test_key_123"
        assert context.session == session
        assert context.is_authenticated
        assert context.ncfa_cookie == "test_cookie"
        assert context.user_id == "user123"
        assert context.username == "testuser"

    def test_user_context_with_expired_session(self):
        """Test user context with an expired session."""
        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="testuser",
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
        )

        context = UserContext(api_key="test_key_123", session=session)

        # Session is present but not valid
        assert context.session == session
        assert not context.is_authenticated  # Expired session = not authenticated

    def test_user_context_repr(self):
        """Test string representation of user context."""
        context = UserContext(api_key="test_key_123")
        repr_str = repr(context)

        assert "UserContext" in repr_str
        assert "not authenticated" in repr_str

        session = UserSession(
            ncfa_cookie="test_cookie",
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        context_with_session = UserContext(api_key="test_key_123", session=session)
        repr_with_session = repr(context_with_session)

        assert "authenticated" in repr_with_session
        assert "user123" in repr_with_session

    def test_user_context_consistent_ids(self):
        """Test that user IDs are consistent for the same API key."""
        context1 = UserContext(api_key="same_key")
        context2 = UserContext(api_key="same_key")

        # Same API key should produce same anonymous user ID
        assert context1.user_id == context2.user_id
        assert context1.username == context2.username

    def test_user_context_different_ids_for_different_keys(self):
        """Test that different API keys produce different anonymous user IDs."""
        context1 = UserContext(api_key="key1")
        context2 = UserContext(api_key="key2")

        # Different API keys should produce different anonymous user IDs
        assert context1.user_id != context2.user_id
        assert context1.username != context2.username
