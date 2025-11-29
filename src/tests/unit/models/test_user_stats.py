"""
A set of tests for the UserStats model.

This module is responsible for testing functionalities of the UserStats
model, including testing the creation of model instances from API
responses, handling alternative field names in the API data, and
serialization of model instances into dictionaries.
"""

from geoguessr_mcp.models import UserStats


class TestUserStats:
    """Tests for UserStats model."""

    def test_from_api_response(self, mock_stats_data):
        """Test creating stats from API response."""
        stats = UserStats.from_api_response(mock_stats_data)

        assert stats.games_played == 100
        assert stats.rounds_played == 500
        assert stats.total_score == 2250000
        assert stats.average_score == 22500
        assert stats.perfect_games == 10
        assert stats.win_rate == 0.65
        assert stats.streak_best == 25

    def test_from_api_response_alternative_fields(self):
        """Test handling alternative field names."""
        data = {
            "totalGames": 50,
            "totalRounds": 250,
            "score": 1000000,
            "fiveKs": 5,
            "countryStreakBest": 15,
        }
        stats = UserStats.from_api_response(data)

        assert stats.games_played == 50
        assert stats.rounds_played == 250
        assert stats.total_score == 1000000
        assert stats.perfect_games == 5
        assert stats.streak_best == 15

    def test_to_dict(self, mock_stats_data):
        """Test serializing stats to dict."""
        stats = UserStats.from_api_response(mock_stats_data)
        result = stats.to_dict()

        assert result["games_played"] == 100
        assert "raw_data" not in result
