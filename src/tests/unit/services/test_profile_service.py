"""
Tests for the ProfileService behaviors and functionality.

This module includes tests for various aspects of ProfileService such
as profile management, statistics retrieval, achievement
retrieval, and handling edge cases or failures during service
operations.
"""

import pytest

from geoguessr_mcp.models import Achievement, UserProfile, UserStats


class TestProfileService:
    """Tests for ProfileService."""

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self, profile_service, mock_client, mock_profile_data, mock_dynamic_response
    ):
        """Test successful profile retrieval."""
        mock_client.get.return_value = mock_dynamic_response(mock_profile_data)

        profile, response = await profile_service.get_profile()

        assert isinstance(profile, UserProfile)
        assert profile.id == "test-user-id"
        assert profile.nick == "TestPlayer"
        assert profile.email == "test@example.com"
        assert profile.country == "FR"
        assert profile.level == 50
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile_with_session_token(
        self, profile_service, mock_client, mock_profile_data, mock_dynamic_response
    ):
        """Test profile retrieval with explicit session token."""
        mock_client.get.return_value = mock_dynamic_response(mock_profile_data)

        await profile_service.get_profile(session_token="test_token")

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][1] == "test_token"

    @pytest.mark.asyncio
    async def test_get_profile_failure(self, profile_service, mock_client, mock_dynamic_response):
        """Test profile retrieval failure."""
        mock_client.get.return_value = mock_dynamic_response(
            {"error": "Unauthorized"}, success=False, status_code=401
        )

        with pytest.raises(ValueError, match="Failed to get profile"):
            await profile_service.get_profile()

    @pytest.mark.asyncio
    async def test_get_stats_success(
        self, profile_service, mock_client, mock_stats_data, mock_dynamic_response
    ):
        """Test successful stats retrieval."""
        mock_client.get.return_value = mock_dynamic_response(mock_stats_data)

        stats, response = await profile_service.get_stats()

        assert isinstance(stats, UserStats)
        assert stats.games_played == 100
        assert stats.rounds_played == 500
        assert stats.total_score == 2250000
        assert stats.win_rate == 0.65

    @pytest.mark.asyncio
    async def test_get_stats_failure(self, profile_service, mock_client, mock_dynamic_response):
        """Test stats retrieval failure."""
        mock_client.get.return_value = mock_dynamic_response(
            {"error": "Server error"}, success=False, status_code=500
        )

        with pytest.raises(ValueError, match="Failed to get stats"):
            await profile_service.get_stats()

    @pytest.mark.asyncio
    async def test_get_extended_stats(self, profile_service, mock_client, mock_dynamic_response):
        """Test extended stats retrieval."""
        extended_data = {
            "totalDistance": 1500000,
            "averageTime": 45.5,
            "favoriteMap": "World",
        }
        mock_client.get.return_value = mock_dynamic_response(extended_data)

        response = await profile_service.get_extended_stats()

        assert response.is_success
        assert response.data["totalDistance"] == 1500000

    @pytest.mark.asyncio
    async def test_get_achievements_list_format(
        self, profile_service, mock_client, mock_dynamic_response
    ):
        """Test achievements retrieval with list format response."""
        achievements_data = [
            {
                "id": "ach-1",
                "name": "First Win",
                "description": "Win your first game",
                "unlocked": True,
                "unlockedAt": "2024-01-15T00:00:00Z",
            },
            {
                "id": "ach-2",
                "name": "Explorer",
                "description": "Play 100 games",
                "unlocked": False,
                "progress": 0.45,
            },
        ]
        mock_client.get.return_value = mock_dynamic_response(achievements_data)

        achievements, response = await profile_service.get_achievements()

        assert len(achievements) == 2
        assert all(isinstance(a, Achievement) for a in achievements)
        assert achievements[0].name == "First Win"
        assert achievements[0].unlocked is True
        assert achievements[1].unlocked is False

    @pytest.mark.asyncio
    async def test_get_achievements_dict_format(
        self, profile_service, mock_client, mock_dynamic_response
    ):
        """Test achievements retrieval with dict format response."""
        achievements_data = {
            "achievements": [
                {"id": "ach-1", "name": "Winner", "unlocked": True},
            ]
        }
        mock_client.get.return_value = mock_dynamic_response(achievements_data)

        achievements, response = await profile_service.get_achievements()

        assert len(achievements) == 1
        assert achievements[0].name == "Winner"

    @pytest.mark.asyncio
    async def test_get_public_profile(self, profile_service, mock_client, mock_dynamic_response):
        """Test public profile retrieval."""
        public_profile_data = {
            "id": "other-user-123",
            "nick": "OtherPlayer",
            "country": "US",
            "level": 75,
        }
        mock_client.get.return_value = mock_dynamic_response(public_profile_data)

        profile, response = await profile_service.get_public_profile("other-user-123")

        assert profile.id == "other-user-123"
        assert profile.nick == "OtherPlayer"

    @pytest.mark.asyncio
    async def test_get_user_maps(self, profile_service, mock_client, mock_dynamic_response):
        """Test user maps retrieval."""
        maps_data = [
            {"id": "map-1", "name": "My Custom Map"},
            {"id": "map-2", "name": "Another Map"},
        ]
        mock_client.get.return_value = mock_dynamic_response(maps_data)

        response = await profile_service.get_user_maps()

        assert response.is_success
        assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_get_comprehensive_profile_success(
        self,
        profile_service,
        mock_client,
        mock_profile_data,
        mock_stats_data,
        mock_dynamic_response,
    ):
        """Test comprehensive profile aggregation."""
        # Setup mock responses for each call
        mock_client.get.side_effect = [
            mock_dynamic_response(mock_profile_data),  # profile
            mock_dynamic_response(mock_stats_data),  # stats
            mock_dynamic_response({"totalDistance": 1000}),  # extended stats
            mock_dynamic_response(
                [  # achievements
                    {"id": "ach-1", "name": "Test", "unlocked": True, "unlockedAt": "2024-01-01"},
                ]
            ),
        ]

        result = await profile_service.get_comprehensive_profile()

        assert result["profile"] is not None
        assert result["profile"]["nick"] == "TestPlayer"
        assert result["stats"] is not None
        assert result["stats"]["games_played"] == 100
        assert result["extended_stats"] is not None
        assert result["achievements"]["total"] == 1
        assert result["achievements"]["unlocked"] == 1
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_get_comprehensive_profile_partial_failure(
        self, profile_service, mock_client, mock_profile_data, mock_dynamic_response
    ):
        """Test comprehensive profile with some endpoints failing."""
        mock_client.get.side_effect = [
            mock_dynamic_response(mock_profile_data),  # profile succeeds
            Exception("Stats endpoint down"),  # stats fails
            mock_dynamic_response({"data": "test"}),  # extended stats succeed
            Exception("Achievements unavailable"),  # achievements fails
        ]

        result = await profile_service.get_comprehensive_profile()

        assert result["profile"] is not None
        assert result["stats"] is None
        assert result["extended_stats"] is not None
        assert result["achievements"] is None
        assert len(result["errors"]) == 2
        assert any("Stats" in e for e in result["errors"])
        assert any("Achievements" in e for e in result["errors"])
