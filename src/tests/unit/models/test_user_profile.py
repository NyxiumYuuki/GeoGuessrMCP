"""Test suite for the UserProfile model.

This module contains a collection of test cases designed to validate
the behavior of the UserProfile model, including creating instances
from API responses and serializing them back into dictionaries.
"""

from geoguessr_mcp.models import UserProfile


class TestUserProfile:
    """Tests for UserProfile model."""

    def test_from_api_response(self, mock_profile_data):
        """Test creating profile from API response."""
        profile = UserProfile.from_api_response(mock_profile_data)

        assert profile.id == "test-user-id"
        assert profile.nick == "TestPlayer"
        assert profile.email == "test@example.com"
        assert profile.country == "FR"
        assert profile.level == 50
        assert profile.is_verified is True
        assert profile.is_pro is True

    def test_from_api_response_minimal(self):
        """Test creating profile from minimal response."""
        data = {"id": "123", "nick": "Player"}
        profile = UserProfile.from_api_response(data)

        assert profile.id == "123"
        assert profile.nick == "Player"
        assert profile.email == ""
        assert profile.level == 0

    def test_to_dict(self, mock_profile_data):
        """Test serializing profile to dict."""
        profile = UserProfile.from_api_response(mock_profile_data)
        result = profile.to_dict()

        assert result["id"] == "test-user-id"
        assert result["nick"] == "TestPlayer"
        assert "raw_data" not in result
