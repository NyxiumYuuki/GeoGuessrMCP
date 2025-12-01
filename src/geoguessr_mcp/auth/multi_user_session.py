"""
Multi-user session management.

This module provides session management for multiple users,
where each API key can have its own GeoGuessr session.
"""

import asyncio
import logging

from ..config import settings
from .session import SessionManager, UserSession
from .user_context import UserContext

logger = logging.getLogger(__name__)


class MultiUserSessionManager:
    """
    Manages GeoGuessr sessions for multiple users.

    Each API key can have its own GeoGuessr session, allowing
    multiple users to access their own accounts through the same
    MCP server instance.
    """

    def __init__(self):
        """Initialize the multi-user session manager."""
        # Map API keys to their session managers
        self._user_managers: dict[str, SessionManager] = {}
        self._lock = asyncio.Lock()

        # Create default session manager if default cookie is configured
        if settings.DEFAULT_NCFA_COOKIE:
            logger.info("Default GeoGuessr cookie configured - will be used as fallback")

    async def get_user_context(self, api_key: str) -> UserContext:
        """
        Get or create a user context for an API key.

        Args:
            api_key: The API key identifying the user

        Returns:
            UserContext: The context for this user
        """
        async with self._lock:
            # Get or create session manager for this user
            if api_key not in self._user_managers:
                # Create new session manager with default cookie as fallback
                self._user_managers[api_key] = SessionManager(
                    default_cookie=settings.DEFAULT_NCFA_COOKIE
                )
                logger.info(f"Created new session manager for API key {api_key[:8]}...")

            manager = self._user_managers[api_key]

        # Get the session (may return default session if no user login)
        session = await manager.get_session()

        # Create user context
        context = UserContext(api_key=api_key, session=session)

        return context

    async def login_user(self, api_key: str, email: str, password: str) -> tuple[str, UserSession]:
        """
        Login a specific user (API key) to their GeoGuessr account.

        Args:
            api_key: The API key identifying the user
            email: GeoGuessr email
            password: GeoGuessr password

        Returns:
            tuple[str, UserSession]: (session_token, UserSession)

        Raises:
            ValueError: If login fails
        """
        async with self._lock:
            if api_key not in self._user_managers:
                self._user_managers[api_key] = SessionManager()

            manager = self._user_managers[api_key]

        # Perform login
        session_token, session = await manager.login(email, password)

        logger.info(f"User {session.username} logged in successfully for API key {api_key[:8]}...")

        return session_token, session

    async def logout_user(self, api_key: str, session_token: str) -> bool:
        """
        Logout a specific user's session.

        Args:
            api_key: The API key identifying the user
            session_token: The session token to logout

        Returns:
            bool: True if logout successful, False otherwise
        """
        async with self._lock:
            if api_key not in self._user_managers:
                return False

            manager = self._user_managers[api_key]

        success = await manager.logout(session_token)

        if success:
            logger.info(f"User logged out for API key {api_key[:8]}...")

        return success

    async def set_user_cookie(self, api_key: str, cookie: str) -> bool:
        """
        Set a GeoGuessr cookie for a specific user.

        Args:
            api_key: The API key identifying the user
            cookie: The NCFA cookie value

        Returns:
            bool: True if cookie is valid, False otherwise
        """
        # Validate cookie first
        profile = await SessionManager.validate_cookie(cookie)
        if not profile:
            return False

        async with self._lock:
            if api_key not in self._user_managers:
                self._user_managers[api_key] = SessionManager()

            manager = self._user_managers[api_key]

        await manager.set_default_cookie(cookie)

        logger.info(
            f"Cookie set for user {profile.get('nick', 'unknown')} (API key {api_key[:8]}...)"
        )

        return True

    async def get_session_for_api_key(self, api_key: str) -> UserSession | None:
        """
        Get the active session for a specific API key.

        Args:
            api_key: The API key identifying the user

        Returns:
            UserSession if available, None otherwise
        """
        async with self._lock:
            if api_key not in self._user_managers:
                return None

            manager = self._user_managers[api_key]

        return await manager.get_session()

    async def get_auth_status(self, api_key: str) -> dict:
        """
        Get authentication status for a specific user.

        Args:
            api_key: The API key identifying the user

        Returns:
            dict: Authentication status information
        """
        context = await self.get_user_context(api_key)

        return {
            "authenticated": context.is_authenticated,
            "user_id": context.user_id if context.is_authenticated else None,
            "username": context.username if context.is_authenticated else None,
            "api_key": f"{api_key[:8]}..." if len(api_key) > 8 else "***",
        }


# Global multi-user session manager instance
multi_user_session_manager = MultiUserSessionManager()
