"""
GeoGuessr API Endpoints Registry.

Centralized endpoint definitions with metadata for dynamic discovery and routing.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from ..config import settings


@dataclass
class EndpointInfo:
    """Metadata about an API endpoint."""
    path: str
    method: str = "GET"
    description: str = ""
    auth_required: bool = True
    use_game_server: bool = False
    params_builder: Optional[Callable[..., dict]] = None


class Endpoints:
    """
    Centralized endpoint registry for GeoGuessr API.

    All endpoints are defined here with their metadata, making it easy to
    maintain and extend the API coverage.
    """

    class AUTH:
        """Authentication endpoints."""
        SIGNIN = EndpointInfo(
            path="/v3/accounts/signin",
            method="POST",
            description="Sign in with email and password",
            auth_required=False,
        )

    class PROFILES:
        """User profile and stats endpoints."""
        GET_PROFILE = EndpointInfo(
            path="/v3/profiles",
            description="Get current user profile",
        )
        GET_STATS = EndpointInfo(
            path="/v3/profiles/stats",
            description="Get user statistics",
        )
        GET_EXTENDED_STATS = EndpointInfo(
            path="/v4/stats/me",
            description="Get extended statistics",
        )
        GET_ACHIEVEMENTS = EndpointInfo(
            path="/v3/profiles/achievements",
            description="Get user achievements",
        )
        GET_USER_MAPS = EndpointInfo(
            path="/v3/profiles/maps",
            description="Get user's custom maps",
        )

        @staticmethod
        def get_public_profile(user_id: str) -> EndpointInfo:
            """Get public profile by user ID."""
            return EndpointInfo(
                path=f"/v3/profiles/{user_id}",
                description=f"Get public profile for user {user_id}",
            )

        @staticmethod
        def get_user_activities(user_id: str) -> EndpointInfo:
            """Get user activities/feed."""
            return EndpointInfo(
                path=f"/v3/users/{user_id}/activities",
                description=f"Get activities for user {user_id}",
            )

    class GAMES:
        """Game-related endpoints."""
        GET_UNFINISHED_GAMES = EndpointInfo(
            path="/v3/social/events/unfinishedgames",
            description="Get unfinished games",
        )

        @staticmethod
        def get_game_details(game_token: str) -> EndpointInfo:
            """Get details for a specific game."""
            return EndpointInfo(
                path=f"/v3/games/{game_token}",
                description=f"Get game details for {game_token}",
            )

        @staticmethod
        def get_streak_game(game_token: str) -> EndpointInfo:
            """Get streak game details."""
            return EndpointInfo(
                path=f"/v3/games/streak/{game_token}",
                description=f"Get streak game {game_token}",
            )

    class GAME_SERVER:
        """Game server endpoints (different base URL)."""
        GET_TOURNAMENTS = EndpointInfo(
            path="/tournaments",
            use_game_server=True,
            description="Get tournament information",
        )

        @staticmethod
        def get_battle_royale(game_id: str) -> EndpointInfo:
            """Get battle royale game."""
            return EndpointInfo(
                path=f"/battle-royale/{game_id}",
                use_game_server=True,
                description=f"Get battle royale game {game_id}",
            )

        @staticmethod
        def get_duel(duel_id: str) -> EndpointInfo:
            """Get duel details."""
            return EndpointInfo(
                path=f"/duels/{duel_id}",
                use_game_server=True,
                description=f"Get duel {duel_id}",
            )

        @staticmethod
        def get_lobby(game_id: str) -> EndpointInfo:
            """Get lobby information."""
            return EndpointInfo(
                path=f"/lobby/{game_id}",
                use_game_server=True,
                description=f"Get lobby {game_id}",
            )

    class COMPETITIVE:
        """Competitive and season-related endpoints."""
        GET_ACTIVE_SEASON_STATS = EndpointInfo(
            path="/v4/seasons/active/stats",
            description="Get active season statistics",
        )

        @staticmethod
        def get_season_game(game_mode: str) -> EndpointInfo:
            """Get season game for specific mode."""
            return EndpointInfo(
                path=f"/v4/seasons/game/{game_mode}",
                description=f"Get season game for mode {game_mode}",
            )

    class CHALLENGES:
        """Challenge-related endpoints."""

        @staticmethod
        def get_daily_challenge(endpoint: str = "today") -> EndpointInfo:
            """Get daily challenge."""
            return EndpointInfo(
                path=f"/v3/challenges/daily-challenges/{endpoint}",
                description=f"Get daily challenge: {endpoint}",
            )

        @staticmethod
        def get_challenge(challenge_token: str) -> EndpointInfo:
            """Get challenge details."""
            return EndpointInfo(
                path=f"/v3/challenges/{challenge_token}",
                description=f"Get challenge {challenge_token}",
            )

    class SOCIAL:
        """Social and friends endpoints."""
        GET_FRIENDS_SUMMARY = EndpointInfo(
            path="/v3/social/friends/summary",
            description="Get friends summary",
        )
        GET_UNCLAIMED_BADGES = EndpointInfo(
            path="/v3/social/badges/unclaimed",
            description="Get unclaimed badges",
        )
        GET_PERSONALIZED_MAPS = EndpointInfo(
            path="/v3/social/maps/browse/personalized",
            description="Get personalized map recommendations",
        )

        @staticmethod
        def get_activity_feed(count: int = 10, page: int = 0) -> EndpointInfo:
            """Get user activity feed."""
            return EndpointInfo(
                path="/v4/feed/private",
                description="Get private activity feed",
                params_builder=lambda: {"count": count, "page": page},
            )

        @staticmethod
        def get_friends_activities(
            time_frame: str = "week", limit: int = 20
        ) -> EndpointInfo:
            """Get friends' activities."""
            return EndpointInfo(
                path="/v3/social/friends/activities",
                description="Get friends' activities",
                params_builder=lambda: {"timeFrame": time_frame, "limit": limit},
            )

    class MAPS:
        """Map-related endpoints."""
        GET_PERSONALIZED_MAPS = EndpointInfo(
            path="/v3/social/maps/browse/personalized",
            description="Get personalized maps",
        )

        @staticmethod
        def get_map_details(map_id: str) -> EndpointInfo:
            """Get map details."""
            return EndpointInfo(
                path=f"/maps/{map_id}",
                description=f"Get map {map_id}",
            )

        @staticmethod
        def get_map_leaderboard(map_id: str) -> EndpointInfo:
            """Get leaderboard for a map."""
            return EndpointInfo(
                path=f"/v3/scores/maps/{map_id}",
                description=f"Get leaderboard for map {map_id}",
            )

        @staticmethod
        def search_maps(
            search_type: str = "all",
            query: str = "",
            count: int = 20,
            page: int = 0,
        ) -> EndpointInfo:
            """Search for maps."""
            return EndpointInfo(
                path=f"/v3/social/maps/browse/{search_type}",
                description=f"Search maps: {search_type}",
                params_builder=lambda: {"q": query, "count": count, "page": page},
            )

    class EXPLORER:
        """Explorer mode endpoints."""
        GET_PROGRESS = EndpointInfo(
            path="/v3/explorer",
            description="Get explorer mode progress",
        )

    class OBJECTIVES:
        """Objectives and rewards endpoints."""
        GET_OBJECTIVES = EndpointInfo(
            path="/v4/objectives",
            description="Get current objectives",
        )
        GET_UNCLAIMED = EndpointInfo(
            path="/v4/objectives/unclaimed",
            description="Get unclaimed objective rewards",
        )

    class SUBSCRIPTION:
        """Subscription-related endpoints."""
        GET_INFO = EndpointInfo(
            path="/v3/subscriptions",
            description="Get subscription details",
        )


class EndpointBuilder:
    """Utility class for building complete URLs."""

    @staticmethod
    def build_url(endpoint: EndpointInfo) -> str:
        """
        Build complete URL for an endpoint.

        Args:
            endpoint: The endpoint info

        Returns:
            Complete URL string
        """
        base = (
            settings.GAME_SERVER_URL
            if endpoint.use_game_server
            else settings.GEOGUESSR_API_URL
        )
        return f"{base}{endpoint.path}"

    @staticmethod
    def is_game_server_endpoint(path: str) -> bool:
        """Check if a path belongs to game server."""
        game_server_prefixes = [
            "/battle-royale/",
            "/duels/",
            "/lobby/",
            "/tournaments",
        ]
        return any(path.startswith(prefix) for prefix in game_server_prefixes)
