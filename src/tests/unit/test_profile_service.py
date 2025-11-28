"""Unit tests for ProfileService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from geoguessr_mcp.models.profile import UserProfile
from geoguessr_mcp.services.profile_service import ProfileService
from geoguessr_mcp.config import settings


class TestProfileService:
    """Tests for ProfileService."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, mock_session, mock_profile_data):
        """Test successful profile retrieval."""
        # Create mock client
        mock_client = MagicMock()
        mock_client.base_url = settings.GEOGUESSR_BASE_URL
        mock_client.get_async_session = AsyncMock(return_value=mock_session)

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_profile_data
        mock_response.raise_for_status = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)

        # Test
        service = ProfileService(mock_client)
        profile = await service.get_profile()

        assert isinstance(profile, UserProfile)
        assert profile.nick == "TestPlayer"
        assert profile.id == "test-user-id"

    @pytest.mark.asyncio
    async def test_get_my_stats_success(self, mock_session, mock_profile_data):
        """Test successful stats retrieval."""
        # Create mock client
        mock_client = MagicMock()
        mock_client.base_url = settings.GEOGUESSR_BASE_URL
        mock_client.get_async_session = AsyncMock(return_value=mock_session)

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_profile_data
        mock_response.raise_for_status = MagicMock()

        mock_session.get = AsyncMock(return_value=mock_response)

        service = ProfileService(mock_client)
        profile = await service.get_stats()

        assert isinstance(profile, UserProfile)
        assert profile. == 100
        assert result["averageScore"] == 4500

    @pytest.mark.asyncio
    async def test_get_extended_stats(self, mock_session):
        """Test extended stats retrieval."""
        from server import get_extended_stats

        extended_stats = {
            "totalGames": 150,
            "winRate": 0.65,
            "averageTime": 180
        }

        with patch("server.get_async_session") as mock_get_session:
            mock_http_response = MagicMock()
            mock_http_response.json.return_value = extended_stats
            mock_http_response.raise_for_status = MagicMock()

            mock_session.get = AsyncMock(return_value=mock_http_response)
            mock_get_session.return_value = mock_session

            result = await get_extended_stats()

            assert result["totalGames"] == 150
            assert result["winRate"] == 0.65
