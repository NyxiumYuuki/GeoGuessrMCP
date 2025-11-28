"""
GeoGuessr MCP Server
A Model Context Protocol server for analyzing GeoGuessr account data.

Supports two authentication modes:
1. Environment variable: Set GEOGUESSR_NCFA_COOKIE for single-user/server-wide auth
2. Per-user login: Use the login tool with email/password to get a session
"""

import os
import sys
import json
import logging
import hashlib
import secrets
from typing import Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GeoGuessr API configuration
GEOGUESSR_BASE_URL = "https://www.geoguessr.com/api"
GAME_SERVER_URL = "https://game-server.geoguessr.com/api"


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check for environment variable (optional now)
    if not os.environ.get("GEOGUESSR_NCFA_COOKIE"):
        logger.info("No GEOGUESSR_NCFA_COOKIE set. Users can authenticate via the 'login' tool.")
    else:
        logger.info("GEOGUESSR_NCFA_COOKIE found. Default authentication available.")

    # Get transport from environment or default to streamable-http for remote access
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    logger.info(f"Starting GeoGuessr MCP Server on {host}:{port} with {transport} transport")
    logger.info("Authentication methods available:")
    logger.info("  1. 'login' tool - authenticate with email/password")
    logger.info("  2. 'set_ncfa_cookie' tool - set cookie manually")
    logger.info("  3. GEOGUESSR_NCFA_COOKIE env var - server-wide default")

    # Initialize FastMCP server
    mcp = FastMCP(
        "GeoGuessr Analyzer",
        instructions="MCP server for analyzing GeoGuessr game statistics and account data",
        host=host,
        port=port
    )

    mcp.run(transport=transport)


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@dataclass
class UserSession:
    """Represents an authenticated GeoGuessr session."""
    ncfa_cookie: str
    user_id: str
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if the session is still valid."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return bool(self.ncfa_cookie)


class SessionManager:
    """Manages user sessions for the MCP server."""

    def __init__(self):
        self._sessions: dict[str, UserSession] = {}  # session_token -> UserSession
        self._user_sessions: dict[str, str] = {}  # user_id -> session_token
        self._default_cookie: Optional[str] = os.environ.get("GEOGUESSR_NCFA_COOKIE")
        self._lock = asyncio.Lock()

    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    async def login(self, email: str, password: str) -> tuple[str, UserSession]:
        """
        Authenticate with GeoGuessr and create a session.
        Returns (session_token, UserSession) on success.
        Raises ValueError on authentication failure.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Attempt to sign in
            response = await client.post(
                f"{GEOGUESSR_BASE_URL}/v3/accounts/signin",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 401:
                raise ValueError("Invalid email or password")
            elif response.status_code == 403:
                raise ValueError("Account access denied. Please check your credentials or try again later.")
            elif response.status_code == 429:
                raise ValueError("Too many login attempts. Please try again later.")
            elif response.status_code != 200:
                raise ValueError(f"Login failed with status {response.status_code}: {response.text}")

            # Extract the _ncfa cookie from response
            ncfa_cookie = None
            for cookie in response.cookies.jar:
                if cookie.name == "_ncfa":
                    ncfa_cookie = cookie.value
                    break

            if not ncfa_cookie:
                # Sometimes the cookie is in Set-Cookie header
                set_cookie = response.headers.get("set-cookie", "")
                if "_ncfa=" in set_cookie:
                    # Parse _ncfa value from Set-Cookie header
                    for part in set_cookie.split(";"):
                        if part.strip().startswith("_ncfa="):
                            ncfa_cookie = part.strip()[6:]
                            break

            if not ncfa_cookie:
                raise ValueError("Authentication succeeded but no session cookie received")

            # Get a user profile with the new cookie
            client.cookies.set("_ncfa", ncfa_cookie, domain="www.geoguessr.com")
            profile_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")

            if profile_response.status_code != 200:
                raise ValueError("Failed to retrieve user profile after login")

            profile = profile_response.json()

            # Create session
            session = UserSession(
                ncfa_cookie=ncfa_cookie,
                user_id=profile.get("id", ""),
                username=profile.get("nick", ""),
                email=email,
                expires_at=datetime.utcnow() + timedelta(days=30)  # Sessions typically last ~30 days
            )

            # Store session
            async with self._lock:
                session_token = self._generate_session_token()

                # Remove old session for this user if exists
                if session.user_id in self._user_sessions:
                    old_token = self._user_sessions[session.user_id]
                    self._sessions.pop(old_token, None)

                self._sessions[session_token] = session
                self._user_sessions[session.user_id] = session_token

            logger.info(f"User {session.username} logged in successfully")
            return session_token, session

    async def logout(self, session_token: str) -> bool:
        """Logout and invalidate a session."""
        async with self._lock:
            if session_token in self._sessions:
                session = self._sessions.pop(session_token)
                self._user_sessions.pop(session.user_id, None)
                logger.info(f"User {session.username} logged out")
                return True
            return False

    async def get_session(self, session_token: Optional[str] = None) -> Optional[UserSession]:
        """Get a session by token, or return default if available."""
        if session_token:
            async with self._lock:
                session = self._sessions.get(session_token)
                if session and session.is_valid():
                    return session
                elif session:
                    # Session expired, clean up
                    self._sessions.pop(session_token, None)
                    self._user_sessions.pop(session.user_id, None)

        # Fall back to default cookie from environment
        if self._default_cookie:
            return UserSession(
                ncfa_cookie=self._default_cookie,
                user_id="default",
                username="default",
                email="default@env"
            )

        return None

    def get_ncfa_cookie(self, session_token: Optional[str] = None) -> str:
        """Synchronous method to get cookie for backward compatibility."""
        if session_token and session_token in self._sessions:
            session = self._sessions[session_token]
            if session.is_valid():
                return session.ncfa_cookie

        if self._default_cookie:
            return self._default_cookie

        raise ValueError(
            "No valid session. Please either:\n"
            "1. Set GEOGUESSR_NCFA_COOKIE environment variable, or\n"
            "2. Use the 'login' tool to authenticate with your GeoGuessr credentials"
        )

    async def list_sessions(self) -> list[dict]:
        """List all active sessions (for admin purposes)."""
        async with self._lock:
            return [
                {
                    "username": s.username,
                    "user_id": s.user_id,
                    "created_at": s.created_at.isoformat(),
                    "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                    "is_valid": s.is_valid()
                }
                for s in self._sessions.values()
            ]


# Global session manager
session_manager = SessionManager()

# Current session token (for simple single-user scenarios via tools)
# In a real multi-user setup, this would be passed via context/headers
_current_session_token: Optional[str] = None


async def get_async_session(session_token: Optional[str] = None) -> httpx.AsyncClient:
    """Create an async HTTP client with authentication."""
    token = session_token or _current_session_token
    session = await session_manager.get_session(token)

    if not session:
        raise ValueError(
            "Not authenticated. Please either:\n"
            "1. Set GEOGUESSR_NCFA_COOKIE environment variable, or\n"
            "2. Use the 'login' tool to authenticate with your GeoGuessr credentials"
        )

    client = httpx.AsyncClient(timeout=30.0)
    client.cookies.set("_ncfa", session.ncfa_cookie, domain="www.geoguessr.com")
    return client


# ============================================================================
# AUTHENTICATION TOOLS
# ============================================================================

@mcp.tool()
async def login(email: str, password: str) -> dict:
    """
    Authenticate with GeoGuessr using your email and password.
    This creates a session that will be used for all subsequent API calls.

    Args:
        email: Your GeoGuessr account email
        password: Your GeoGuessr account password

    Returns:
        Session information including username and session token

    Note: Your credentials are only used to obtain an authentication token
    from GeoGuessr. They are not stored on the server.
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
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }


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
            "message": "Successfully logged out" if success else "No active session to logout"
        }

    return {
        "success": False,
        "message": "No active session"
    }


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
            "username": session.username
        }

    return {
        "success": False,
        "error": "Invalid or expired session token"
    }


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
            return {
                "success": False,
                "error": "Invalid cookie - authentication failed"
            }

        profile = response.json()

        # Create a session from the cookie
        session = UserSession(
            ncfa_cookie=cookie,
            user_id=profile.get("id", ""),
            username=profile.get("nick", ""),
            email="manual@cookie",
            expires_at=datetime.utcnow() + timedelta(days=30)
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
            "session_token": session_token
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
                "expires_at": session.expires_at.isoformat() if session.expires_at else None
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
                        "user_id": profile.get("id", "Unknown")
                    }
        except Exception:
            pass

    return {
        "authenticated": False,
        "message": "Not authenticated. Use 'login' with your GeoGuessr credentials or 'set_ncfa_cookie' with a valid cookie."
    }


# ============================================================================
# PROFILE TOOLS
# ============================================================================

@mcp.tool()
async def get_my_profile() -> dict:
    """
    Get the profile information of the currently logged-in GeoGuessr user.
    Returns user details including username, country, level, and basic stats.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_my_stats() -> dict:
    """
    Get detailed statistics for the currently logged-in user.
    Returns stats displayed on the profile page including games played,
    average scores, and performance metrics.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/stats")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_extended_stats() -> dict:
    """
    Get extended statistics for the currently logged-in user.
    Returns additional stats not shown on the main profile page.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/stats/me")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_my_achievements() -> dict:
    """
    Get all achievements for the currently logged-in user.
    Returns completed and in-progress achievements.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/achievements")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_my_trophies(user_id: Optional[str] = None) -> dict:
    """
    Get trophies for a user. If no user_id is provided, gets trophies for the logged-in user.

    Args:
        user_id: Optional user ID. If not provided, uses the logged-in user.
    """
    async with await get_async_session() as client:
        if user_id:
            url = f"{GEOGUESSR_BASE_URL}/v4/trophies/{user_id}"
        else:
            profile_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")
            profile_response.raise_for_status()
            profile = profile_response.json()
            user_id = profile.get("id")
            url = f"{GEOGUESSR_BASE_URL}/v4/trophies/{user_id}"

        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_trophy_case(user_id: Optional[str] = None) -> dict:
    """
    Get the trophy case (selected/displayed trophies) for a user.

    Args:
        user_id: Optional user ID. If not provided, uses the logged-in user.
    """
    async with await get_async_session() as client:
        if user_id:
            url = f"{GEOGUESSR_BASE_URL}/v4/trophies/{user_id}/case"
        else:
            profile_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")
            profile_response.raise_for_status()
            profile = profile_response.json()
            user_id = profile.get("id")
            url = f"{GEOGUESSR_BASE_URL}/v4/trophies/{user_id}/case"

        response = await client.get(url)
        response.raise_for_status()
        return response.json()


# ============================================================================
# ACTIVITY & GAMES TOOLS
# ============================================================================

@mcp.tool()
async def get_activity_feed(count: int = 20, page: int = 0) -> dict:
    """
    Get the activity feed (games played, achievements, etc.) for the logged-in user.
    This includes game tokens that can be used to fetch detailed game information.

    Args:
        count: Number of activities to return (default: 20)
        page: Page number for pagination (default: 0)
    """
    async with await get_async_session() as client:
        response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v4/feed/private",
            params={"count": count, "page": page}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_game_details(game_token: str) -> dict:
    """
    Get detailed information about a specific game including rounds, scores, and locations.

    Args:
        game_token: The game token/ID (found in game URLs or activity feed)
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/games/{game_token}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_unfinished_games() -> dict:
    """
    Get list of unfinished games for the logged-in user.
    Returns games that were started but not completed.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/social/events/unfinishedgames")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_streak_game(game_token: str) -> dict:
    """
    Get details of a country streak game.

    Args:
        game_token: The streak game token
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/games/streak/{game_token}")
        response.raise_for_status()
        return response.json()


# ============================================================================
# BATTLE ROYALE & COMPETITIVE TOOLS
# ============================================================================

@mcp.tool()
async def get_battle_royale_game(game_id: str) -> dict:
    """
    Get statistics for a Battle Royale game.

    Args:
        game_id: The Battle Royale game ID
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GAME_SERVER_URL}/battle-royale/{game_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_duel_game(duel_id: str) -> dict:
    """
    Get information about a duel game.

    Args:
        duel_id: The duel game ID
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GAME_SERVER_URL}/duels/{duel_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_game_lobby(game_id: str) -> dict:
    """
    Get lobby information for a game including players and their stats.

    Args:
        game_id: The game ID
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GAME_SERVER_URL}/lobby/{game_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_current_season_stats() -> dict:
    """
    Get statistics for the current competitive season.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/seasons/active/stats")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_season_game_info(game_mode: str = "BattleRoyaleCountries") -> dict:
    """
    Get season information for a specific game mode.

    Args:
        game_mode: One of "BattleRoyaleCountries", "BattleRoyaleDistance", or "BattleRoyaleDuels"
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/seasons/game/{game_mode}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_tournaments() -> dict:
    """
    Get information about current and past tournaments.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GAME_SERVER_URL}/tournaments")
        response.raise_for_status()
        return response.json()


# ============================================================================
# CHALLENGES TOOLS
# ============================================================================

@mcp.tool()
async def get_daily_challenge(which: str = "today") -> dict:
    """
    Get information about the daily challenge.

    Args:
        which: Either "today" for today's challenge or "previous" for previous challenges
    """
    async with await get_async_session() as client:
        endpoint = "today" if which == "today" else "previous"
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/challenges/daily-challenges/{endpoint}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_challenge_details(challenge_token: str) -> dict:
    """
    Get detailed information about a specific challenge.

    Args:
        challenge_token: The challenge token/ID
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/challenges/{challenge_token}")
        response.raise_for_status()
        return response.json()


# ============================================================================
# SOCIAL TOOLS
# ============================================================================

@mcp.tool()
async def get_friends(count: int = 50, page: int = 0) -> dict:
    """
    Get the friends list for the logged-in user.

    Args:
        count: Number of friends to return (default: 50)
        page: Page number for pagination (default: 0)
    """
    async with await get_async_session() as client:
        response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v3/social/friends",
            params={"count": count, "page": page}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_friends_summary() -> dict:
    """
    Get friends list along with friend requests and recommendations.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/social/friends/summary")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_notifications(count: int = 20, page: int = 0) -> dict:
    """
    Get notifications for the logged-in user.

    Args:
        count: Number of notifications to return (default: 20)
        page: Page number for pagination (default: 0)
    """
    async with await get_async_session() as client:
        response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v4/notifications",
            params={"count": count, "page": page}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_user(query: str) -> dict:
    """
    Search for a GeoGuessr user by name.

    Args:
        query: The search query (username to search for)
    """
    async with await get_async_session() as client:
        response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v3/search/user",
            params={"q": query}
        )
        response.raise_for_status()
        return response.json()


# ============================================================================
# MAPS TOOLS
# ============================================================================

@mcp.tool()
async def get_my_maps() -> dict:
    """
    Get maps created by the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/maps")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_liked_maps(count: int = 50, page: int = 0) -> dict:
    """
    Get maps liked by the logged-in user.

    Args:
        count: Number of maps to return (default: 50)
        page: Page number for pagination (default: 0)
    """
    async with await get_async_session() as client:
        response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v3/likes",
            params={"count": count, "page": page}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_map_info(map_id: str) -> dict:
    """
    Get information about a specific map.

    Args:
        map_id: The map ID or slug (e.g., "world", "famous-places", or a UUID)
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/maps/{map_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_popular_maps(category: str = "all") -> dict:
    """
    Get popular maps.

    Args:
        category: One of "all", "official", or "featured"
    """
    async with await get_async_session() as client:
        if category == "featured":
            url = f"{GEOGUESSR_BASE_URL}/v3/social/maps/browse/featured"
        elif category == "official":
            url = f"{GEOGUESSR_BASE_URL}/v3/social/maps/browse/popular/official"
        else:
            url = f"{GEOGUESSR_BASE_URL}/v3/social/maps/browse/popular/all"

        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_personalized_maps() -> dict:
    """
    Get personalized map recommendations for the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/social/maps/browse/personalized")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_map_scores(map_id: str) -> dict:
    """
    Get high scores for a specific map.

    Args:
        map_id: The map ID
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/scores/maps/{map_id}")
        response.raise_for_status()
        return response.json()


# ============================================================================
# EXPLORER MODE TOOLS
# ============================================================================

@mcp.tool()
async def get_explorer_progress() -> dict:
    """
    Get explorer mode progress for the logged-in user.
    Shows which countries/regions have been explored.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/explorer")
        response.raise_for_status()
        return response.json()


# ============================================================================
# OBJECTIVES & BADGES TOOLS
# ============================================================================

@mcp.tool()
async def get_objectives() -> dict:
    """
    Get current objectives for the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/objectives")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_unclaimed_objectives() -> dict:
    """
    Get unclaimed objective rewards for the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/objectives/unclaimed")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_unclaimed_badges() -> dict:
    """
    Get unclaimed badges for the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/social/badges/unclaimed")
        response.raise_for_status()
        return response.json()


# ============================================================================
# SUBSCRIPTION & ACCOUNT TOOLS
# ============================================================================

@mcp.tool()
async def get_subscription_info() -> dict:
    """
    Get subscription information for the logged-in user.
    """
    async with await get_async_session() as client:
        response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/subscriptions")
        response.raise_for_status()
        return response.json()


# ============================================================================
# ANALYSIS TOOLS
# ============================================================================

@mcp.tool()
async def analyze_recent_games(count: int = 10) -> dict:
    """
    Analyze recent games and provide statistics summary.
    Fetches recent games from the activity feed and calculates aggregate statistics.

    Args:
        count: Number of recent games to analyze (default: 10)
    """
    async with await get_async_session() as client:
        # Get activity feed
        feed_response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v4/feed/private",
            params={"count": count * 2, "page": 0}
        )
        feed_response.raise_for_status()
        feed = feed_response.json()

        games_analyzed = []
        total_score = 0
        total_rounds = 0
        perfect_rounds = 0

        for entry in feed.get("entries", []):
            if entry.get("type") == "PlayedGame" and len(games_analyzed) < count:
                game_token = entry.get("payload", {}).get("gameToken")
                if game_token:
                    try:
                        game_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/games/{game_token}")
                        if game_response.status_code == 200:
                            game = game_response.json()

                            game_info = {
                                "token": game_token,
                                "map": game.get("map", {}).get("name", "Unknown"),
                                "mode": game.get("type", "Unknown"),
                                "total_score": 0,
                                "rounds": []
                            }

                            for round_data in game.get("player", {}).get("guesses", []):
                                round_score = round_data.get("roundScoreInPoints", 0)
                                game_info["total_score"] += round_score
                                game_info["rounds"].append({
                                    "score": round_score,
                                    "distance": round_data.get("distanceInMeters", 0),
                                    "time": round_data.get("time", 0)
                                })

                                total_rounds += 1
                                if round_score == 5000:
                                    perfect_rounds += 1

                            total_score += game_info["total_score"]
                            games_analyzed.append(game_info)
                    except Exception as e:
                        logger.warning(f"Failed to fetch game {game_token}: {e}")

        return {
            "games_analyzed": len(games_analyzed),
            "total_score": total_score,
            "average_score": total_score / len(games_analyzed) if games_analyzed else 0,
            "total_rounds": total_rounds,
            "perfect_rounds": perfect_rounds,
            "perfect_round_percentage": (perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0,
            "games": games_analyzed
        }


@mcp.tool()
async def get_performance_summary() -> dict:
    """
    Get a comprehensive performance summary combining profile stats,
    achievements, and season information.
    """
    async with await get_async_session() as client:
        results = {}

        # Get profile
        try:
            profile_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")
            profile_response.raise_for_status()
            results["profile"] = profile_response.json()
        except Exception as e:
            results["profile_error"] = str(e)

        # Get stats
        try:
            stats_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/stats")
            stats_response.raise_for_status()
            results["stats"] = stats_response.json()
        except Exception as e:
            results["stats_error"] = str(e)

        # Get extended stats
        try:
            extended_response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/stats/me")
            extended_response.raise_for_status()
            results["extended_stats"] = extended_response.json()
        except Exception as e:
            results["extended_stats_error"] = str(e)

        # Get season stats
        try:
            season_response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/seasons/active/stats")
            season_response.raise_for_status()
            results["current_season"] = season_response.json()
        except Exception as e:
            results["season_error"] = str(e)

        # Get achievements
        try:
            achievements_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/achievements")
            achievements_response.raise_for_status()
            achievements = achievements_response.json()
            results["achievements_summary"] = {
                "total": len(achievements) if isinstance(achievements, list) else 0,
                "achievements": achievements
            }
        except Exception as e:
            results["achievements_error"] = str(e)

        return results
