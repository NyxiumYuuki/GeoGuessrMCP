"""
Tools for handling authentication and session management with GeoGuessr.

This module provides utilities for login, logout, setting authentication cookies,
and checking the current authentication status. With multi-user support, each
API key can have its own GeoGuessr session.

The module integrates with FastMCP to expose authentication methods as tools
and uses the multi-user session manager for per-user session storage.

Functions
---------

- register_auth_tools: Registers a set of authentication tools with FastMCP.

"""

import logging

from mcp.server.fastmcp import FastMCP

from ..auth import get_current_user_context, multi_user_session_manager

logger = logging.getLogger(__name__)


def register_auth_tools(mcp: FastMCP, session_manager=None):
    """
    Register authentication-related tools.

    Note: session_manager parameter is kept for backward compatibility but not used.
    The multi_user_session_manager is used instead.
    """

    @mcp.tool()
    async def login(email: str, password: str) -> dict:
        """
        Authenticate with GeoGuessr using email and password.

        Creates a session for YOUR account that will be used for all later API calls.
        Your credentials are only used to get an authentication token and are
        not stored on the server.

        Each API key gets its own session, so multiple users can use the same
        MCP server with their own GeoGuessr accounts.

        Args:
            email: Your GeoGuessr account email
            password: Your GeoGuessr account password

        Returns:
            Session information including username and session token
        """
        # Get the current user's context (API key)
        user_context = get_current_user_context()
        if not user_context:
            return {
                "success": False,
                "error": "No user context available. Authentication is required.",
            }

        try:
            # Login using the multi-user session manager
            session_token, session = await multi_user_session_manager.login_user(
                user_context.api_key, email, password
            )

            return {
                "success": True,
                "message": f"Successfully logged in as {session.username}",
                "username": session.username,
                "user_id": session.user_id,
                "session_token": session_token,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "multi_user_note": "Your session is tied to your API key. Other users with different API keys can have their own sessions.",
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    @mcp.tool()
    async def logout(session_token: str) -> dict:
        """
        Logout from your current GeoGuessr session.

        Invalidates your session token. This only affects your session
        (tied to your API key), not other users.

        Args:
            session_token: The session token to logout (from login response)

        Returns:
            Success status
        """
        # Get the current user's context
        user_context = get_current_user_context()
        if not user_context:
            return {"success": False, "error": "No user context available"}

        success = await multi_user_session_manager.logout_user(user_context.api_key, session_token)

        return {
            "success": success,
            "message": "Successfully logged out" if success else "No active session found",
        }

    @mcp.tool()
    async def set_ncfa_cookie(cookie: str) -> dict:
        """
        Set the _ncfa cookie for authentication.

        Use this if you've manually extracted the cookie from your browser.
        The cookie will be validated before being accepted.

        This cookie will be tied to YOUR API key, so it won't affect other users.

        Args:
            cookie: The _ncfa cookie value from your browser

        Returns:
            Success status and user information
        """
        # Get the current user's context
        user_context = get_current_user_context()
        if not user_context:
            return {"success": False, "error": "No user context available"}

        # Set the cookie for this user
        success = await multi_user_session_manager.set_user_cookie(user_context.api_key, cookie)

        if not success:
            return {"success": False, "error": "Invalid cookie - authentication failed"}

        # Get updated session to show user info
        session = await multi_user_session_manager.get_session_for_api_key(user_context.api_key)

        if session:
            return {
                "success": True,
                "message": f"Cookie set successfully. Authenticated as {session.username}",
                "username": session.username,
                "user_id": session.user_id,
            }

        return {"success": True, "message": "Cookie set successfully"}

    @mcp.tool()
    async def get_auth_status() -> dict:
        """
        Check your current authentication status.

        Returns information about your session (tied to your API key).
        Each user with a different API key has their own independent session.

        Returns:
            Authentication status and user information
        """
        # Get the current user's context
        user_context = get_current_user_context()
        if not user_context:
            return {
                "authenticated": False,
                "message": "No user context available",
            }

        # Get auth status for this user
        status = await multi_user_session_manager.get_auth_status(user_context.api_key)

        if status["authenticated"]:
            return {
                **status,
                "message": f"Authenticated as {status['username']}",
                "multi_user_info": "Your session is independent. Other API keys have their own sessions.",
            }

        return {
            **status,
            "message": "Not authenticated. Use 'login' with credentials or 'set_ncfa_cookie' with a valid cookie.",
            "available_methods": ["login(email, password)", "set_ncfa_cookie(cookie)"],
        }


def get_current_session_token():
    """
    Deprecated: This function is no longer used in multi-user mode.

    Sessions are now managed per-API-key automatically.
    Use get_current_user_context() instead to access user-specific session data.
    """
    logger.warning(
        "get_current_session_token() is deprecated in multi-user mode. "
        "Use get_current_user_context() instead."
    )
    return None
