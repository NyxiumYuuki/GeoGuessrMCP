"""Auth module for GeoGuessr session."""

from .multi_user_session import MultiUserSessionManager, multi_user_session_manager
from .request_context import (
    get_current_user_context,
    require_user_context,
    set_current_user_context,
)
from .session import SessionManager, UserSession
from .user_context import UserContext

__all__ = [
    "UserSession",
    "SessionManager",
    "UserContext",
    "MultiUserSessionManager",
    "multi_user_session_manager",
    "get_current_user_context",
    "require_user_context",
    "set_current_user_context",
]
