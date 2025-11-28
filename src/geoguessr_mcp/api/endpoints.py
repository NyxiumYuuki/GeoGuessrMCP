"""
Geoguessr API Endpoints
Centralized endpoint definitions extracted from the Geoguessr API.

"""
from ..config import settings


class Endpoints:
    """
    Centralized endpoint registry for Geoguessr API.

    Usage:
        url = Endpoints.PROFILES.GET_PROFILE
        full_url = f"{GEOGUESSR_BASE_URL}{url}"
    """

    # ============================================================================
    # AUTHENTICATION ENDPOINTS
    # ============================================================================
    class AUTH:
        """Authentication endpoints."""
        SIGNIN = "/v3/accounts/signin"  # POST

    # ============================================================================
    # PROFILE ENDPOINTS
    # ============================================================================
    class PROFILES:
        """User profile and stats endpoints."""
        GET_PROFILE = "/v3/profiles"  # GET - Get current user profile
        GET_STATS = "/v3/profiles/stats"  # GET - Get user statistics
        GET_EXTENDED_STATS = "/v4/stats/me"  # GET - Get extended statistics
        GET_ACHIEVEMENTS = "/v3/profiles/achievements"  # GET - Get user achievements
        GET_USER_MAPS = "/v3/profiles/maps"  # GET - Get user's custom maps

        @staticmethod
        def get_public_profile(user_id: str) -> str:
            """Get public profile by user ID."""
            return f"/v3/profiles/{user_id}"

        @staticmethod
        def get_user_activities(user_id: str) -> str:
            """Get user activities/feed."""
            return f"/v3/users/{user_id}/activities"

    # ============================================================================
    # GAME ENDPOINTS
    # ============================================================================
    class GAMES:
        """Game-related endpoints."""
        GET_UNFINISHED_GAMES = "/v3/social/events/unfinishedgames"  # GET

        @staticmethod
        def get_game_details(game_token: str) -> str:
            """Get details for a specific game."""
            return f"/v3/games/{game_token}"

        @staticmethod
        def get_streak_game(game_token: str) -> str:
            """Get streak game details."""
            return f"/v3/games/streak/{game_token}"

    # ============================================================================
    # GAME SERVER ENDPOINTS (Different base URL)
    # ============================================================================
    class GAME_SERVER:
        """Game server endpoints (use GAME_SERVER_URL as base)."""
        GET_TOURNAMENTS = "/tournaments"  # GET

        @staticmethod
        def get_battle_royale(game_id: str) -> str:
            """Get battle royale game."""
            return f"/battle-royale/{game_id}"

        @staticmethod
        def get_duel(duel_id: str) -> str:
            """Get duel details."""
            return f"/duels/{duel_id}"

        @staticmethod
        def get_lobby(game_id: str) -> str:
            """Get lobby information."""
            return f"/lobby/{game_id}"

    # ============================================================================
    # COMPETITIVE/SEASONS ENDPOINTS
    # ============================================================================
    class COMPETITIVE:
        """Competitive and season-related endpoints."""
        GET_ACTIVE_SEASON_STATS = "/v4/seasons/active/stats"  # GET

        @staticmethod
        def get_season_game(game_mode: str) -> str:
            """Get season game for specific mode."""
            return f"/v4/seasons/game/{game_mode}"

    # ============================================================================
    # CHALLENGE ENDPOINTS
    # ============================================================================
    class CHALLENGES:
        """Challenge-related endpoints."""

        @staticmethod
        def get_daily_challenge(endpoint: str = "current") -> str:
            """
            Get daily challenge.

            Args:
                endpoint: 'current', 'today', or specific date
            """
            return f"/v3/challenges/daily-challenges/{endpoint}"

        @staticmethod
        def get_challenge(challenge_token: str) -> str:
            """Get challenge details."""
            return f"/v3/challenges/{challenge_token}"

    # ============================================================================
    # SOCIAL/FRIENDS ENDPOINTS
    # ============================================================================
    class SOCIAL:
        """Social and friends endpoints."""
        GET_FRIENDS_SUMMARY = "/v3/social/friends/summary"  # GET
        GET_UNCLAIMED_BADGES = "/v3/social/badges/unclaimed"  # GET
        GET_PERSONALIZED_MAPS = "/v3/social/maps/browse/personalized"  # GET

        @staticmethod
        def get_activity_feed(count: int = 10, page: int = 0) -> tuple[str, dict]:
            """
            Get user activity feed.

            Returns:
                Tuple of (endpoint, params_dict)
            """
            return "/v4/feed/private", {"count": count, "page": page}

        @staticmethod
        def get_friends_activities(time_frame: str, limit: int = 20) -> tuple[str, dict]:
            """
            Get friends' activities.

            Args:
                time_frame: Time frame for activities
                limit: Maximum number of activities

            Returns:
                Tuple of (endpoint, params_dict)
            """
            return "/v3/social/friends/activities", {"timeFrame": time_frame, "limit": limit}

    # ============================================================================
    # MAPS ENDPOINTS
    # ============================================================================
    class MAPS:
        """Map-related endpoints."""
        GET_PERSONALIZED_MAPS = "/v3/social/maps/browse/personalized"  # GET

        @staticmethod
        def get_map_details(map_id: str) -> str:
            """Get map details."""
            return f"/maps/{map_id}"

        @staticmethod
        def get_map_leaderboard(map_id: str) -> str:
            """Get leaderboard for a map."""
            return f"/v3/scores/maps/{map_id}"

        @staticmethod
        def search_maps(search_type: str, query: str, count: int = 20, page: int = 0) -> tuple[str, dict]:
            """
            Search for maps.

            Args:
                search_type: Type of search ('all', 'official', 'community', etc.)
                query: Search query
                count: Number of results per-page
                page: Page number

            Returns:
                Tuple of (endpoint, params_dict)
            """
            return f"/v3/social/maps/browse/{search_type}", {
                "q": query,
                "count": count,
                "page": page
            }

    # ============================================================================
    # EXPLORER MODE ENDPOINTS
    # ============================================================================
    class EXPLORER:
        """Explorer mode endpoints."""
        GET_PROGRESS = "/v3/explorer"  # GET - Get explorer mode progress

    # ============================================================================
    # OBJECTIVES/REWARDS ENDPOINTS
    # ============================================================================
    class OBJECTIVES:
        """Objectives and rewards endpoints."""
        GET_OBJECTIVES = "/v4/objectives"  # GET - Get current objectives
        GET_UNCLAIMED_OBJECTIVES = "/v4/objectives/unclaimed"  # GET - Get unclaimed rewards

    # ============================================================================
    # SUBSCRIPTION ENDPOINTS
    # ============================================================================
    class SUBSCRIPTION:
        """Subscription-related endpoints."""
        GET_SUBSCRIPTION_INFO = "/v3/subscriptions"  # GET - Get subscription details


# ============================================================================
# ENDPOINT UTILITIES
# ============================================================================

class EndpointBuilder:
    """Utility class for building complete URLs."""

    @staticmethod
    def build_url(endpoint: str, use_game_server: bool = False) -> str:
        """
        Build complete URL for an endpoint.

        Args:
            endpoint: The endpoint path
            use_game_server: Whether to use game server URL

        Returns:
            Complete URL
        """
        base = settings.GAME_SERVER_URL if use_game_server else settings.GEOGUESSR_BASE_URL
        return f"{base}{endpoint}"

    @staticmethod
    def is_game_server_endpoint(endpoint: str) -> bool:
        """
        Check if endpoint belongs to game server.

        Args:
            endpoint: The endpoint path

        Returns:
            True if it's a game server endpoint
        """
        game_server_prefixes = [
            "/battle-royale/",
            "/duels/",
            "/lobby/",
            "/tournaments"
        ]
        return any(endpoint.startswith(prefix) for prefix in game_server_prefixes)


# ============================================================================
# ENDPOINT METADATA
# ============================================================================

ENDPOINT_METADATA = {
    # Profile endpoints
    "/v3/profiles": {
        "method": "GET",
        "description": "Get current user profile",
        "auth_required": True,
        "response_type": "profile"
    },
    "/v3/profiles/stats": {
        "method": "GET",
        "description": "Get user statistics",
        "auth_required": True,
        "response_type": "stats"
    },
    "/v4/stats/me": {
        "method": "GET",
        "description": "Get extended statistics",
        "auth_required": True,
        "response_type": "extended_stats"
    },
    "/v3/profiles/achievements": {
        "method": "GET",
        "description": "Get user achievements",
        "auth_required": True,
        "response_type": "achievements"
    },

    # Game endpoints
    "/v3/games/{game_token}": {
        "method": "GET",
        "description": "Get game details",
        "auth_required": True,
        "response_type": "game"
    },
    "/v3/social/events/unfinishedgames": {
        "method": "GET",
        "description": "Get unfinished games",
        "auth_required": True,
        "response_type": "games_list"
    },

    # Competitive endpoints
    "/v4/seasons/active/stats": {
        "method": "GET",
        "description": "Get active season statistics",
        "auth_required": True,
        "response_type": "season_stats"
    },

    # Social endpoints
    "/v4/feed/private": {
        "method": "GET",
        "description": "Get private activity feed",
        "auth_required": True,
        "response_type": "feed",
        "params": ["count", "page"]
    },
    "/v3/social/friends/summary": {
        "method": "GET",
        "description": "Get friends summary",
        "auth_required": True,
        "response_type": "friends"
    },

    # Maps endpoints
    "/maps/{map_id}": {
        "method": "GET",
        "description": "Get map details",
        "auth_required": False,
        "response_type": "map"
    },
    "/v3/scores/maps/{map_id}": {
        "method": "GET",
        "description": "Get map leaderboard",
        "auth_required": True,
        "response_type": "leaderboard"
    },

    # Explorer endpoints
    "/v3/explorer": {
        "method": "GET",
        "description": "Get explorer mode progress",
        "auth_required": True,
        "response_type": "explorer"
    },

    # Objectives endpoints
    "/v4/objectives": {
        "method": "GET",
        "description": "Get current objectives",
        "auth_required": True,
        "response_type": "objectives"
    },
}


def get_endpoint_info(endpoint: str) -> dict:
    """
    Get metadata for an endpoint.

    Args:
        endpoint: The endpoint path

    Returns:
        Dictionary with endpoint metadata
    """
    return ENDPOINT_METADATA.get(endpoint, {
        "method": "GET",
        "description": "Unknown endpoint",
        "auth_required": True,
        "response_type": "unknown"
    })
