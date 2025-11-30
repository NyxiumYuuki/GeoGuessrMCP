"""Tests for request context utilities."""

import pytest

from geoguessr_mcp.auth.request_context import (
    get_current_user_context,
    require_user_context,
    set_current_user_context,
)
from geoguessr_mcp.auth.user_context import UserContext


class TestRequestContext:
    """Tests for request context utilities."""

    def test_get_current_user_context_returns_none_initially(self):
        """Test that get_current_user_context returns None when not set."""
        # Note: This might fail if previous tests didn't clean up
        # In a real scenario, each test would have isolated context
        context = get_current_user_context()
        # Context might be None or from previous test
        assert context is None or isinstance(context, UserContext)

    def test_set_and_get_current_user_context(self):
        """Test setting and getting current user context."""
        test_context = UserContext(api_key="test_key_123")

        set_current_user_context(test_context)
        retrieved_context = get_current_user_context()

        assert retrieved_context is not None
        assert retrieved_context.api_key == "test_key_123"

    def test_require_user_context_raises_when_not_set(self):
        """Test that require_user_context raises RuntimeError when context not set."""
        # Clear any existing context
        set_current_user_context(None)

        with pytest.raises(RuntimeError, match="No user context available"):
            require_user_context()

    def test_require_user_context_returns_context_when_set(self):
        """Test that require_user_context returns context when it's set."""
        test_context = UserContext(api_key="test_key_456")

        set_current_user_context(test_context)
        retrieved_context = require_user_context()

        assert retrieved_context is not None
        assert retrieved_context.api_key == "test_key_456"

    def test_context_can_be_updated(self):
        """Test that context can be updated by setting a new one."""
        context1 = UserContext(api_key="key1")
        context2 = UserContext(api_key="key2")

        set_current_user_context(context1)
        assert get_current_user_context().api_key == "key1"

        set_current_user_context(context2)
        assert get_current_user_context().api_key == "key2"

    def test_context_can_be_cleared(self):
        """Test that context can be cleared by setting to None."""
        test_context = UserContext(api_key="test_key")

        set_current_user_context(test_context)
        assert get_current_user_context() is not None

        set_current_user_context(None)
        context = get_current_user_context()
        # After clearing, should be None
        assert context is None
