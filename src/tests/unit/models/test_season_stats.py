"""
Tests for the SeasonStats model.

This module includes test cases to verify the functionality of the SeasonStats
model, especially its method for creating an instance from an API response.
The tests validate proper handling of fields and alternative field names in
the response.

Classes:
    TestSeasonStats: Contains test cases for the SeasonStats model.
"""

from geoguessr_mcp.models import SeasonStats


class TestSeasonStats:
    """Tests for SeasonStats model."""

    def test_from_api_response(self, mock_season_stats_response):
        """Test creating season stats from API response."""
        stats = SeasonStats.from_api_response(mock_season_stats_response)

        assert stats.season_id == "season-2024-1"
        assert stats.season_name == "Season 1 2024"
        assert stats.rank == 150
        assert stats.rating == 1850
        assert stats.games_played == 45
        assert stats.wins == 30
        assert stats.division == "Gold"

    def test_from_api_response_alternative_fields(self):
        """Test handling alternative field names."""
        data = {
            "id": "s1",
            "name": "Season One",
            "position": 100,
            "elo": 1500,
            "games": 20,
            "tier": "Silver",
        }
        stats = SeasonStats.from_api_response(data)

        assert stats.season_id == "s1"
        assert stats.rank == 100
        assert stats.rating == 1500
        assert stats.division == "Silver"
