"""
A module for testing the functionalities of `GameService` in the GeoGuessr
ecosystem.

This module contains a collection of test cases designed to validate
the correctness, edge cases, and error handling for various
asynchronous methods in the `GameService` class. These include
retrieving game details, unfinished games, streak games, activity
feeds, recent games, season statistics, and daily challenges.
"""

import pytest

from geoguessr_mcp.models import DailyChallenge, Game, SeasonStats


class TestGameService:
    """Tests for GameService."""

    @pytest.mark.asyncio
    async def test_get_game_details_success(
        self, game_service, mock_client, mock_game_data, mock_dynamic_response
    ):
        """Test successful game details retrieval."""
        mock_client.get.return_value = mock_dynamic_response(mock_game_data)

        game, response = await game_service.get_game_details("ABC123")

        assert isinstance(game, Game)
        assert game.token == "ABC123"
        assert game.map_name == "World"
        assert game.mode == "standard"
        assert len(game.rounds) == 5
        assert game.total_score == 23200  # Sum of all round scores

    @pytest.mark.asyncio
    async def test_get_game_details_with_session_token(
        self, game_service, mock_client, mock_game_data, mock_dynamic_response
    ):
        """Test game details with explicit session token."""
        mock_client.get.return_value = mock_dynamic_response(mock_game_data)

        game, response = await game_service.get_game_details("ABC123", session_token="test_token")

        call_args = mock_client.get.call_args
        assert call_args[0][1] == "test_token"

    @pytest.mark.asyncio
    async def test_get_game_details_failure(self, game_service, mock_client, mock_dynamic_response):
        """Test game details retrieval failure."""
        mock_client.get.return_value = mock_dynamic_response(
            {"error": "Game not found"}, success=False, status_code=404
        )

        with pytest.raises(ValueError, match="Failed to get game details"):
            await game_service.get_game_details("INVALID")

    @pytest.mark.asyncio
    async def test_get_unfinished_games(self, game_service, mock_client, mock_dynamic_response):
        """Test unfinished games retrieval."""
        unfinished_data = [
            {"token": "game-1", "map": {"name": "World"}},
            {"token": "game-2", "map": {"name": "Europe"}},
        ]
        mock_client.get.return_value = mock_dynamic_response(unfinished_data)

        response = await game_service.get_unfinished_games()

        assert response.is_success
        assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_get_streak_game(self, game_service, mock_client, mock_dynamic_response):
        """Test streak game retrieval."""
        streak_data = {
            "token": "streak-123",
            "currentStreak": 15,
            "bestStreak": 25,
        }
        mock_client.get.return_value = mock_dynamic_response(streak_data)

        response = await game_service.get_streak_game("streak-123")

        assert response.is_success
        assert response.data["currentStreak"] == 15

    @pytest.mark.asyncio
    async def test_get_activity_feed(
        self, game_service, mock_client, mock_activity_feed_data, mock_dynamic_response
    ):
        """Test activity feed retrieval."""
        mock_client.get.return_value = mock_dynamic_response(mock_activity_feed_data)

        response = await game_service.get_activity_feed(count=10, page=0)

        assert response.is_success
        assert len(response.data["entries"]) == 3

    @pytest.mark.asyncio
    async def test_get_activity_feed_pagination(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test activity feed with pagination."""
        page_2_data = {"entries": [{"type": "PlayedGame", "payload": {"gameToken": "old-game"}}]}
        mock_client.get.return_value = mock_dynamic_response(page_2_data)

        response = await game_service.get_activity_feed(count=10, page=1)

        assert response.is_success
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_games_success(
        self,
        game_service,
        mock_client,
        mock_activity_feed_data,
        mock_game_data,
        mock_dynamic_response,
    ):
        """Test recent games retrieval."""
        # First call returns activity feed, subsequent calls return game details
        mock_client.get.side_effect = [
            mock_dynamic_response(mock_activity_feed_data),
            mock_dynamic_response(mock_game_data),
            mock_dynamic_response({**mock_game_data, "token": "game-token-2"}),
        ]

        games = await game_service.get_recent_games(count=2)

        assert len(games) == 2
        assert all(isinstance(g, Game) for g in games)

    @pytest.mark.asyncio
    async def test_get_recent_games_empty_feed(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test recent games with empty activity feed."""
        mock_client.get.return_value = mock_dynamic_response({"entries": []})

        games = await game_service.get_recent_games(count=5)

        assert len(games) == 0

    @pytest.mark.asyncio
    async def test_get_recent_games_feed_failure(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test recent games when feed fails."""
        mock_client.get.return_value = mock_dynamic_response({"error": "Failed"}, success=False)

        games = await game_service.get_recent_games(count=5)

        assert len(games) == 0

    @pytest.mark.asyncio
    async def test_get_recent_games_skips_failed_game_fetch(
        self,
        game_service,
        mock_client,
        mock_activity_feed_data,
        mock_game_data,
        mock_dynamic_response,
    ):
        """Test that failed individual game fetches are skipped."""
        mock_client.get.side_effect = [
            mock_dynamic_response(mock_activity_feed_data),
            Exception("Game fetch failed"),  # First game fails
            mock_dynamic_response(mock_game_data),  # Second game succeeds
        ]

        games = await game_service.get_recent_games(count=2)

        assert len(games) == 1

    @pytest.mark.asyncio
    async def test_get_season_stats_success(
        self, game_service, mock_client, mock_season_stats_data, mock_dynamic_response
    ):
        """Test season stats retrieval."""
        mock_client.get.return_value = mock_dynamic_response(mock_season_stats_data)

        stats, response = await game_service.get_season_stats()

        assert isinstance(stats, SeasonStats)
        assert stats.season_id == "season-2024-1"
        assert stats.rank == 150
        assert stats.rating == 1850
        assert stats.division == "Gold"

    @pytest.mark.asyncio
    async def test_get_season_stats_failure(self, game_service, mock_client, mock_dynamic_response):
        """Test season stats failure."""
        mock_client.get.return_value = mock_dynamic_response(
            {"error": "No active season"}, success=False, status_code=404
        )

        with pytest.raises(ValueError, match="Failed to get season stats"):
            await game_service.get_season_stats()

    @pytest.mark.asyncio
    async def test_get_daily_challenge_today(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test daily challenge retrieval for today."""
        challenge_data = {
            "token": "daily-2024-01-15",
            "map": {"name": "World"},
            "date": "2024-01-15",
            "timeLimit": 180,
        }
        mock_client.get.return_value = mock_dynamic_response(challenge_data)

        challenge, response = await game_service.get_daily_challenge()

        assert isinstance(challenge, DailyChallenge)
        assert challenge.token == "daily-2024-01-15"
        assert challenge.time_limit == 180

    @pytest.mark.asyncio
    async def test_get_daily_challenge_specific_day(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test daily challenge for specific day."""
        challenge_data = {
            "token": "daily-2024-01-10",
            "date": "2024-01-10",
        }
        mock_client.get.return_value = mock_dynamic_response(challenge_data)

        challenge, response = await game_service.get_daily_challenge(day="2024-01-10")

        assert challenge.date == "2024-01-10"

    @pytest.mark.asyncio
    async def test_get_daily_challenge_failure(
        self, game_service, mock_client, mock_dynamic_response
    ):
        """Test daily challenge failure."""
        mock_client.get.return_value = mock_dynamic_response(
            {"error": "Challenge not found"}, success=False, status_code=404
        )

        with pytest.raises(ValueError, match="Failed to get daily challenge"):
            await game_service.get_daily_challenge()

    @pytest.mark.asyncio
    async def test_get_battle_royale(self, game_service, mock_client, mock_dynamic_response):
        """Test battle royale game retrieval."""
        br_data = {
            "gameId": "br-123",
            "players": 10,
            "status": "in_progress",
        }
        mock_client.get.return_value = mock_dynamic_response(br_data)

        response = await game_service.get_battle_royale("br-123")

        assert response.is_success
        assert response.data["players"] == 10

    @pytest.mark.asyncio
    async def test_get_duel(self, game_service, mock_client, mock_dynamic_response):
        """Test duel game retrieval."""
        duel_data = {
            "duelId": "duel-456",
            "player1": {"id": "p1", "score": 5000},
            "player2": {"id": "p2", "score": 4500},
        }
        mock_client.get.return_value = mock_dynamic_response(duel_data)

        response = await game_service.get_duel("duel-456")

        assert response.is_success
        assert response.data["player1"]["score"] == 5000

    @pytest.mark.asyncio
    async def test_get_tournaments(self, game_service, mock_client, mock_dynamic_response):
        """Test tournaments retrieval."""
        tournaments_data = [
            {"id": "t1", "name": "Weekly Tournament", "status": "active"},
            {"id": "t2", "name": "Monthly Cup", "status": "upcoming"},
        ]
        mock_client.get.return_value = mock_dynamic_response(tournaments_data)

        response = await game_service.get_tournaments()

        assert response.is_success
        assert len(response.data) == 2
