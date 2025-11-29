"""
Unit tests for validating the functionality of the Game model and related components.

These tests ensure the proper creation and behavior of Game and RoundGuess
instances when interacting with API responses or performing operations like
serialization. The tests cover both standard and edge cases.
"""

from geoguessr_mcp.models.Game import Game
from geoguessr_mcp.models.RoundGuess import RoundGuess


class TestGame:
    """Tests for Game model."""

    def test_from_api_response(self, mock_game_data):
        """Test creating game from API response."""
        game = Game.from_api_response(mock_game_data)

        assert game.token == "ABC123"
        assert game.map_name == "World"
        assert game.mode == "standard"
        assert game.finished is True
        assert len(game.rounds) == 5
        assert game.total_score == 5000 + 4500 + 3800 + 4900 + 5000

    def test_from_api_response_minimal(self):
        """Test creating game from minimal response."""
        data = {
            "token": "TEST",
            "type": "challenge",
            "player": {"guesses": []},
        }
        game = Game.from_api_response(data)

        assert game.token == "TEST"
        assert game.mode == "challenge"
        assert game.total_score == 0
        assert len(game.rounds) == 0

    def test_round_guess(self):
        """Test creating round guess."""
        data = {
            "roundScoreInPoints": 4500,
            "distanceInMeters": 150.5,
            "time": 25,
        }
        guess = RoundGuess.from_api_response(data, round_num=1)

        assert guess.round_number == 1
        assert guess.score == 4500
        assert guess.distance_meters == 150.5
        assert guess.time_seconds == 25

    def test_to_dict(self, mock_game_data):
        """Test serializing game to dict."""
        game = Game.from_api_response(mock_game_data)
        result = game.to_dict()

        assert result["token"] == "ABC123"
        assert len(result["rounds"]) == 5
        assert result["total_score"] > 0
