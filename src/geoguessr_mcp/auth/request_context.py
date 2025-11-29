"""
Request context utilities for accessing user context in tools.

This module provides utilities to access the current user context
from within MCP tools, allowing each tool to operate on behalf of
the authenticated user making the request.
"""

from contextvars import ContextVar
from typing import Optional

from .user_context import UserContext

# Context variable to store the current user context
_current_user_context: ContextVar[Optional[UserContext]] = ContextVar(
    "current_user_context", default=None
)


def set_current_user_context(context: UserContext) -> None:
    """
    Set the current user context for this request.

    This should be called by middleware to set the context
    for the duration of the request.

    Args:
        context: The UserContext for the current request
    """
    _current_user_context.set(context)


def get_current_user_context() -> Optional[UserContext]:
    """
    Get the current user context.

    This can be called from within tools to access the user context
    for the current request.

    Returns:
        UserContext if available, None otherwise
    """
    return _current_user_context.get()


def require_user_context() -> UserContext:
    """
    Get the current user context, raising an error if not available.

    Raises:
        RuntimeError: If no user context is available

    Returns:
        UserContext: The current user context
    """
    context = get_current_user_context()
    if context is None:
        raise RuntimeError(
            "No user context available. This tool must be called through the MCP server."
        )
    return context
