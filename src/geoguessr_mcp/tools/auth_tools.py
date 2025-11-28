"""MCP tools for auth operations."""

import logging

from mcp.server.fastmcp import FastMCP

from ..auth.session import SessionManager

logger = logging.getLogger(__name__)


def register_auth_tools(mcp: FastMCP, session_manager: SessionManager):
    """Register auth-related tools."""

    @mcp.tool()
    async def login(email: str, password: str) -> dict:
        """
        Authenticate with GeoGuessr using your email and password.
        This creates a session that will be used for all later API calls.

        Args:
            email: Your GeoGuessr account email
            password: Your GeoGuessr account password

        Returns:
            Session information including username and session token

        Note: Your credentials are only used to get an authentication token
        from GeoGuessr. They are not stored on the server.
        """

        try:
            session_token, session = await session_manager.login(email, password)

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
        This invalidates the current session token.
        """
        global _current_session_token

        if _current_session_token:
            success = await session_manager.logout(_current_session_token)
            _current_session_token = None
            return {
                "success": success,
                "message": "Successfully logged out" if success else "No active session to logout",
            }

        return {"success": False, "message": "No active session"}

    @mcp.tool()
    async def set_session_token(token: str) -> dict:
        """
        Set an existing session token for authentication.
        Use this if you have a previously obtained session token.

        Args:
            token: A valid session token from a previous login
        """
        global _current_session_token

        session = await session_manager.get_session(token)
        if session and session.is_valid():
            _current_session_token = token
            return {
                "success": True,
                "message": f"Session set for user {session.username}",
                "username": session.username,
            }

        return {"success": False, "error": "Invalid or expired session token"}

    @mcp.tool()
    async def set_ncfa_cookie(cookie: str) -> dict:
        """
        Directly set the _ncfa cookie for authentication.
        Use this if you've manually extracted the cookie from your browser.

        Args:
            cookie: The _ncfa cookie value from your browser

        Note: This sets the cookie as the default for all requests.
        """
        global _current_session_token

        # Validate the cookie by making a test request
        async with httpx.AsyncClient(timeout=30.0) as client:
            client.cookies.set("_ncfa", cookie, domain="www.geoguessr.com")
            response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")

            if response.status_code != 200:
                return {"success": False, "error": "Invalid cookie - authentication failed"}

            profile = response.json()

            # Create a session from the cookie
            session = UserSession(
                ncfa_cookie=cookie,
                user_id=profile.get("id", ""),
                username=profile.get("nick", ""),
                email="manual@cookie",
                expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30),
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
        Returns information about the current session or authentication method.
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
        env_cookie = os.environ.get("GEOGUESSR_NCFA_COOKIE")
        if env_cookie:
            # Validate the environment cookie
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    client.cookies.set("_ncfa", env_cookie, domain="www.geoguessr.com")
                    response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")

                    if response.status_code == 200:
                        profile = response.json()
                        return {
                            "authenticated": True,
                            "method": "environment_variable",
                            "username": profile.get("nick", "Unknown"),
                            "user_id": profile.get("id", "Unknown"),
                        }
            except Exception:
                pass

        return {
            "authenticated": False,
            "message": "Not authenticated. Use 'login' with your GeoGuessr credentials or 'set_ncfa_cookie' with a valid cookie.",
        }
