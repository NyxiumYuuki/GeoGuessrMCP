"""
Tools for handling authentication and session management with GeoGuessr.

This module provides utilities for login, logout, setting authentication cookies,
and checking the current authentication status. Its primary purpose is to ensure
interactions with the GeoGuessr API are authenticated securely and conveniently.

The module integrates with FastMCP to expose authentication methods as tools
and uses the `SessionManager` for session storage and validation.

Functions
---------

- register_auth_tools: Registers a set of authentication tools with FastMCP.
- get_current_session_token: Returns the currently active session token.

"""

import logging
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..auth.session import SessionManager, UserSession
from ..config import settings

logger = logging.getLogger(__name__)

# Global session token storage
_current_session_token: Optional[str] = None


def register_auth_tools(mcp: FastMCP, session_manager: SessionManager):
    """Register authentication-related tools."""

    @mcp.tool()
    async def login(email: str, password: str) -> dict:
        """
        Authenticate with GeoGuessr using email and password.

        Creates a session that will be used for all later API calls.
        Credentials are only used to get an authentication token and are
        not stored on the server.

        Args:
            email: Your GeoGuessr account email
            password: Your GeoGuessr account password

        Returns:
            Session information including username and session token
        """
        global _current_session_token

        try:
            session_token, session = await session_manager.login(email, password)
            _current_session_token = session_token

            return {
                "success": True,
                "message": f"Successfully logged in as {session.username}",
                "username": session.username,
                "user_id": session.user_id,
                "session_token": session_token,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    @mcp.tool()
    async def logout() -> dict:
        """
        Logout from the current GeoGuessr session.

        Invalidates the current session token.
        """
        global _current_session_token

        if _current_session_token:
            success = await session_manager.logout(_current_session_token)
            _current_session_token = None
            return {
                "success": success,
                "message": "Successfully logged out" if success else "No active session found",
            }

        return {"success": False, "message": "No active session"}

    @mcp.tool()
    async def set_ncfa_cookie(cookie: str) -> dict:
        """
        Set the _ncfa cookie for authentication.

        Use this if you've manually extracted the cookie from your browser.
        The cookie will be validated before being accepted.

        Args:
            cookie: The _ncfa cookie value from your browser
        """
        global _current_session_token

        # Validate the cookie
        profile = await session_manager.validate_cookie(cookie)

        if not profile:
            return {"success": False, "error": "Invalid cookie - authentication failed"}

        # Create a session from the cookie
        session = UserSession(
            ncfa_cookie=cookie,
            user_id=profile.get("id", ""),
            username=profile.get("nick", ""),
            email="manual@cookie",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        # Store as a session
        session_token = secrets.token_urlsafe(32)
        async with session_manager._lock:
            session_manager._sessions[session_token] = session
            session_manager._user_sessions[session.user_id] = session_token

        _current_session_token = session_token

        return {
            "success": True,
            "message": f"Cookie set successfully. Authenticated as {session.username}",
            "username": session.username,
            "user_id": session.user_id,
            "session_token": session_token,
        }

    @mcp.tool()
    async def get_auth_status() -> dict:
        """
        Check the current authentication status.

        Returns information about the current session or available
        authentication methods.
        """
        global _current_session_token

        # Check for active session
        if _current_session_token:
            session = await session_manager.get_session(_current_session_token)
            if session and session.is_valid():
                return {
                    "authenticated": True,
                    "method": "session",
                    "username": session.username,
                    "user_id": session.user_id,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                }

        # Check for environment variable
        env_cookie = settings.DEFAULT_NCFA_COOKIE
        if env_cookie:
            profile = await session_manager.validate_cookie(env_cookie)
            if profile:
                return {
                    "authenticated": True,
                    "method": "environment_variable",
                    "username": profile.get("nick", "Unknown"),
                    "user_id": profile.get("id", "Unknown"),
                }

        return {
            "authenticated": False,
            "message": "Not authenticated. Use 'login' with credentials or 'set_ncfa_cookie' with a valid cookie.",
            "available_methods": ["login(email, password)", "set_ncfa_cookie(cookie)"],
        }


def get_current_session_token() -> Optional[str]:
    """Get the current session token for use by other tools."""
    return _current_session_token
