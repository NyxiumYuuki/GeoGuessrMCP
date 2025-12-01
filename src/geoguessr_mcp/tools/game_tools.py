"""
Provide functionality to register game-related tools with the FastMCP server.

The module defines tools that can query various game-related details, including
specific game information, activity feeds, recent games, unfinished games,
season statistics, and details about game modes like daily challenges,
Battle Royale, duels, and tournaments.

Functions:
    register_game_tools: Registers multiple tools to interact with the
    game service and retrieve or manage game-related data.
"""

from mcp.server.fastmcp import FastMCP

from ..services.game_service import GameService
from .auth_tools import get_current_session_token


def register_game_tools(mcp: FastMCP, game_service: GameService):
    """Register game-related tools."""

    @mcp.tool()
    async def get_game_details(game_token: str) -> dict:
        """
        Get detailed information about a specific game.

        Args:
            game_token: The game's token/ID

        Returns:
            Detailed game information including all rounds and scores
        """
        session_token = get_current_session_token()
        game, response = await game_service.get_game_details(game_token, session_token)

        return {
            "game": game.to_dict(),
            "available_fields": response.available_fields,
            "raw_summary": response.summarize(max_depth=2),
        }

    @mcp.tool()
    async def get_activity_feed(count: int = 10, page: int = 0) -> dict:
        """
        Get the user's activity feed.

        Shows recent games, achievements, and other activities.

        Args:
            count: Number of items to fetch (default: 10)
            page: Page number for pagination (default: 0)

        Returns:
            Activity feed entries with dynamic schema information
        """
        session_token = get_current_session_token()
        response = await game_service.get_activity_feed(count, page, session_token)

        if not response.is_success:
            return {"success": False, "error": str(response.data)}

        # Extract and categorize entries
        entries = response.data.get("entries", [])
        categorized = {}

        for entry in entries:
            entry_type = entry.get("type", "unknown")
            if entry_type not in categorized:
                categorized[entry_type] = []
            categorized[entry_type].append(entry)

        return {
            "success": True,
            "total_entries": len(entries),
            "entry_types": list(categorized.keys()),
            "entries_by_type": {t: len(e) for t, e in categorized.items()},
            "recent_entries": entries[:5],  # First 5 for context
            "available_fields": response.available_fields,
        }

    @mcp.tool()
    async def get_recent_games(count: int = 10) -> dict:
        """
        Get recent games with full details.

        Args:
            count: Number of games to retrieve (default: 10)

        Returns:
            List of recent games with scores and round details
        """
        session_token = get_current_session_token()
        games = await game_service.get_recent_games(count, session_token)

        return {
            "games_found": len(games),
            "games": [g.to_dict() for g in games],
            "summary": {
                "total_score": sum(g.total_score for g in games),
                "average_score": sum(g.total_score for g in games) / len(games) if games else 0,
                "maps_played": list({g.map_name for g in games}),
            },
        }

    @mcp.tool()
    async def get_unfinished_games() -> dict:
        """
        Get list of games that haven't been completed.

        Returns:
            List of unfinished games that can be resumed
        """
        session_token = get_current_session_token()
        response = await game_service.get_unfinished_games(session_token)

        return {
            "success": response.is_success,
            "data": response.data if response.is_success else None,
            "available_fields": response.available_fields,
        }

    @mcp.tool()
    async def get_season_stats() -> dict:
        """
        Get current competitive season statistics.

        Returns:
            Season ranking, rating, games played, and division info
        """
        session_token = get_current_session_token()

        try:
            stats, response = await game_service.get_season_stats(session_token)

            return {
                "success": True,
                "season_stats": {
                    "rank": stats.rank,
                    "rating": stats.rating,
                    "games_played": stats.games_played,
                    "wins": stats.wins,
                    "division": stats.division,
                },
                "available_fields": response.available_fields,
                "raw_summary": response.summarize(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_daily_challenge(day: str = "today") -> dict:
        """
        Get information about the daily challenge.

        Args:
            day: "today", "yesterday", or a specific date

        Returns:
            Daily challenge details including map and time limit
        """
        session_token = get_current_session_token()

        try:
            challenge, response = await game_service.get_daily_challenge(day, session_token)

            return {
                "success": True,
                "challenge": {
                    "token": challenge.token,
                    "map": challenge.map_name,
                    "date": challenge.date,
                    "time_limit": challenge.time_limit,
                    "completed": challenge.completed,
                    "score": challenge.score,
                },
                "available_fields": response.available_fields,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_battle_royale(game_id: str) -> dict:
        """
        Get Battle Royale game details.

        Args:
            game_id: The Battle Royale game ID

        Returns:
            Game details including players and standings
        """
        session_token = get_current_session_token()
        response = await game_service.get_battle_royale(game_id, session_token)

        return {
            "success": response.is_success,
            "data": response.summarize() if response.is_success else None,
            "available_fields": response.available_fields,
            "schema_description": response.schema_description,
        }

    @mcp.tool()
    async def get_duel(duel_id: str) -> dict:
        """
        Get Duel game details.

        Args:
            duel_id: The Duel game ID

        Returns:
            Duel details including opponent and results
        """
        session_token = get_current_session_token()
        response = await game_service.get_duel(duel_id, session_token)

        return {
            "success": response.is_success,
            "data": response.summarize() if response.is_success else None,
            "available_fields": response.available_fields,
        }

    @mcp.tool()
    async def get_tournaments() -> dict:
        """
        Get tournament information.

        Returns:
            Available tournaments and their details
        """
        session_token = get_current_session_token()
        response = await game_service.get_tournaments(session_token)

        return {
            "success": response.is_success,
            "data": response.summarize() if response.is_success else None,
            "available_fields": response.available_fields,
        }
