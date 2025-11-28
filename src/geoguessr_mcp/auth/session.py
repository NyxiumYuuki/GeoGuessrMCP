"""
Session management for GeoGuessr authentication.
"""

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Represents an authenticated GeoGuessr session."""

    ncfa_cookie: str
    user_id: str
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if the session is still valid."""
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False
        return bool(self.ncfa_cookie)


class SessionManager:
    """Manages user sessions for the MCP server."""

    def __init__(self, default_cookie: Optional[str] = None):
        self._sessions: dict[str, UserSession] = {}
        self._user_sessions: dict[str, str] = {}
        self._default_cookie: Optional[str] = default_cookie or settings.DEFAULT_NCFA_COOKIE
        self._lock = asyncio.Lock()

    @staticmethod
    def _generate_session_token() -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    async def login(
        self, email: str, password: str, base_url: str = settings.GEOGUESSR_API_URL
    ) -> tuple[str, UserSession]:
        """
        Authenticate with GeoGuessr and create a session.

        Args:
            email: User's email address
            password: User's password
            base_url: GeoGuessr API base URL

        Returns:
            tuple[str, UserSession]: (session_token, UserSession) on success

        Raises:
            ValueError: On authentication failure
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Attempt to sign in
            response = await client.post(
                f"{base_url}/v3/accounts/signin",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 401:
                raise ValueError("Invalid email or password")
            elif response.status_code == 403:
                raise ValueError("Account access denied")
            elif response.status_code == 429:
                raise ValueError("Too many login attempts")
            elif response.status_code != 200:
                raise ValueError(f"Login failed: {response.status_code}")

            # Extract the _ncfa cookie
            ncfa_cookie = self._extract_ncfa_cookie(response)
            if not ncfa_cookie:
                raise ValueError("No session cookie received")

            # Get user profile
            client.cookies.set("_ncfa", ncfa_cookie, domain=settings.GEOGUESSR_DOMAIN_NAME)
            profile_response = await client.get(f"{base_url}/v3/profiles")

            if profile_response.status_code != 200:
                raise ValueError("Failed to retrieve user profile")

            profile = profile_response.json()

            # Create and store session
            session = UserSession(
                ncfa_cookie=ncfa_cookie,
                user_id=profile.get("id", ""),
                username=profile.get("nick", ""),
                email=email,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )

            session_token = await self._store_session(session)
            logger.info(f"User {session.username} logged in successfully")

            return session_token, session

    @staticmethod
    def _extract_ncfa_cookie(response: httpx.Response) -> Optional[str]:
        """Extract _ncfa cookie from response."""
        # Try cookies jar first
        for cookie in response.cookies.jar:
            if cookie.name == "_ncfa":
                return cookie.value

        # Try Set-Cookie header
        set_cookie = response.headers.get("set-cookie", "")
        if "_ncfa=" in set_cookie:
            for part in set_cookie.split(";"):
                if part.strip().startswith("_ncfa="):
                    return part.strip()[6:]

        return None

    async def _store_session(self, session: UserSession) -> str:
        """Store a session and return its token."""
        async with self._lock:
            session_token = self._generate_session_token()

            # Remove old session for this user if exists
            if session.user_id in self._user_sessions:
                old_token = self._user_sessions[session.user_id]
                self._sessions.pop(old_token, None)

            self._sessions[session_token] = session
            self._user_sessions[session.user_id] = session_token

            return session_token

    async def logout(self, session_token: str) -> bool:
        """
        Logout and invalidate a session.

        Args:
            session_token: Token of the session to logout

        Returns:
            bool: True if session was found and removed, False otherwise
        """
        async with self._lock:
            if session_token in self._sessions:
                session = self._sessions.pop(session_token)
                self._user_sessions.pop(session.user_id, None)
                logger.info(f"User {session.username} logged out")
                return True
            return False

    async def get_session(self, session_token: Optional[str] = None) -> Optional[UserSession]:
        """
        Get a session by token or return default if available.

        Args:
            session_token: Optional session token to look up

        Returns:
            UserSession if found and valid, None otherwise
        """
        if session_token:
            async with self._lock:
                session = self._sessions.get(session_token)
                if session and session.is_valid():
                    return session
                elif session:
                    # Session expired, clean up
                    self._sessions.pop(session_token, None)
                    self._user_sessions.pop(session.user_id, None)

        # Fall back to default cookie if available
        if self._default_cookie:
            return UserSession(
                ncfa_cookie=self._default_cookie,
                user_id="default",
                username="default",
                email="default",
            )

        return None

    async def set_default_cookie(self, cookie: str) -> None:
        """
        Set or update the default NCFA cookie.

        Args:
            cookie: The NCFA cookie value to set as default
        """
        async with self._lock:
            self._default_cookie = cookie
            logger.info("Default NCFA cookie updated")

    @staticmethod
    async def validate_cookie(cookie: str) -> Optional[dict]:
        """
        Validate a cookie by making a test request.

        Returns:
            User profile dict if valid, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                client.cookies.set("_ncfa", cookie, domain=settings.GEOGUESSR_DOMAIN_NAME)
                response = await client.get(
                    f"{settings.GEOGUESSR_API_URL}/v3/profiles"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Cookie validation failed: {e}")
        return None
