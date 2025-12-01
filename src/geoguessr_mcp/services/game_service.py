"""
Game service for game data operations.

Handles game history, details, and competitive data with dynamic schema support.
"""

import logging

from ..api import DynamicResponse, Endpoints, GeoGuessrClient
from ..models import DailyChallenge, Game, SeasonStats

logger = logging.getLogger(__name__)


class GameService:
    """Service for game-related operations."""

    def __init__(self, client: GeoGuessrClient):
        self.client = client

    async def get_game_details(
        self,
        game_token: str,
            session_token: str | None = None,
    ) -> tuple[Game, DynamicResponse]:
        """
        Get details for a specific game.

        Args:
            game_token: The game token/ID
            session_token: Optional session token

        Returns:
            Tuple of (Game, DynamicResponse)
        """
        endpoint = Endpoints.GAMES.get_game_details(game_token)
        response = await self.client.get(endpoint, session_token)

        if response.is_success:
            game = Game.from_api_response(response.data)
            return game, response

        raise ValueError(f"Failed to get game details: {response.data}")

    async def get_unfinished_games(
        self,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get list of unfinished games."""
        return await self.client.get(Endpoints.GAMES.GET_UNFINISHED_GAMES, session_token)

    async def get_streak_game(
        self,
        game_token: str,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get streak game details."""
        endpoint = Endpoints.GAMES.get_streak_game(game_token)
        return await self.client.get(endpoint, session_token)

    async def get_activity_feed(
        self,
        count: int = 10,
        page: int = 0,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """
        Get the activity feed.

        Args:
            count: Number of items to fetch
            page: Page number for pagination
            session_token: Optional session token

        Returns:
            DynamicResponse with feed data
        """
        endpoint = Endpoints.SOCIAL.get_activity_feed(count, page)
        return await self.client.get(endpoint, session_token)

    async def get_recent_games(
        self,
        count: int = 10,
            session_token: str | None = None,
    ) -> list[Game]:
        """
        Get recent games from the activity feed.

        Args:
            count: Number of games to retrieve
            session_token: Optional session token

        Returns:
            List of Game objects
        """
        feed_response = await self.get_activity_feed(count * 2, 0, session_token)

        if not feed_response.is_success:
            return []

        games = []
        entries = feed_response.data.get("entries", [])

        for entry in entries:
            if len(games) >= count:
                break

            entry_type = entry.get("type", "")
            if entry_type in ["PlayedGame", "FinishedGame", "game"]:
                payload = entry.get("payload", entry)
                game_token = payload.get("gameToken", payload.get("token"))

                if game_token:
                    try:
                        game, _ = await self.get_game_details(game_token, session_token)
                        games.append(game)
                    except Exception as e:
                        logger.warning(f"Failed to fetch game {game_token}: {e}")

        return games

    async def get_season_stats(
        self,
            session_token: str | None = None,
    ) -> tuple[SeasonStats, DynamicResponse]:
        """Get active season statistics."""
        response = await self.client.get(
            Endpoints.COMPETITIVE.GET_ACTIVE_SEASON_STATS, session_token
        )

        if response.is_success:
            stats = SeasonStats.from_api_response(response.data)
            return stats, response

        raise ValueError(f"Failed to get season stats: {response.data}")

    async def get_daily_challenge(
        self,
        day: str = "today",
            session_token: str | None = None,
    ) -> tuple[DailyChallenge, DynamicResponse]:
        """
        Get daily challenge.

        Args:
            day: "today", "yesterday", or specific date
            session_token: Optional session token

        Returns:
            Tuple of (DailyChallenge, DynamicResponse)
        """
        endpoint = Endpoints.CHALLENGES.get_daily_challenge(day)
        response = await self.client.get(endpoint, session_token)

        if response.is_success:
            challenge = DailyChallenge.from_api_response(response.data)
            return challenge, response

        raise ValueError(f"Failed to get daily challenge: {response.data}")

    async def get_battle_royale(
        self,
        game_id: str,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get battle royale game details."""
        endpoint = Endpoints.GAME_SERVER.get_battle_royale(game_id)
        return await self.client.get(endpoint, session_token)

    async def get_duel(
        self,
        duel_id: str,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get duel game details."""
        endpoint = Endpoints.GAME_SERVER.get_duel(duel_id)
        return await self.client.get(endpoint, session_token)

    async def get_tournaments(
        self,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get tournament information."""
        return await self.client.get(Endpoints.GAME_SERVER.GET_TOURNAMENTS, session_token)
