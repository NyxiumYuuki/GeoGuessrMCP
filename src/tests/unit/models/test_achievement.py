"""
Tests for the Achievement model.

This module provides integration tests to verify that the Achievement
model behaves correctly when constructed using API response data. It
includes scenarios for both locked and unlocked achievements with relevant
data transformations.
"""

from geoguessr_mcp.models import Achievement


class TestAchievement:
    """Tests for Achievement model."""

    def test_from_api_response_unlocked(self):
        """Test creating unlocked achievement."""
        data = {
            "id": "ach-1",
            "name": "First Steps",
            "description": "Complete your first game",
            "unlocked": True,
            "unlockedAt": "2024-01-15T00:00:00.000Z",
        }
        achievement = Achievement.from_api_response(data)

        assert achievement.id == "ach-1"
        assert achievement.name == "First Steps"
        assert achievement.unlocked is True
        assert achievement.unlocked_at == "2024-01-15T00:00:00.000Z"

    def test_from_api_response_locked(self):
        """Test creating locked achievement with progress."""
        data = {
            "id": "ach-2",
            "name": "Explorer",
            "description": "Play 100 games",
            "unlocked": False,
            "progress": 0.45,
        }
        achievement = Achievement.from_api_response(data)

        assert achievement.id == "ach-2"
        assert achievement.unlocked is False
        assert achievement.progress == 0.45
