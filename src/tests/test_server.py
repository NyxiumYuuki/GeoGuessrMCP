"""
Tests for GeoGuessr MCP Server
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


# Mock the environment variable before importing server
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("GEOGUESSR_NCFA_COOKIE", "test_cookie_value")


class TestProfileTools:
    """Tests for profile-related tools."""

    @pytest.mark.asyncio
    async def test_get_my_profile_success(self):
        """Test successful profile retrieval."""
        from server import get_my_profile

        mock_response = {
            "id": "test-user-id",
            "nick": "TestPlayer",
            "country": "US",
            "level": 50,
        }

        with patch("server.get_async_session") as mock_session:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_response
            mock_http_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_session.return_value = mock_client

            result = await get_my_profile()

            assert result["nick"] == "TestPlayer"
            assert result["id"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_get_my_stats_success(self):
        """Test successful stats retrieval."""
        from server import get_my_stats

        mock_response = {
            "gamesPlayed": 100,
            "averageScore": 4500,
            "highScore": 5000,
        }

        with patch("server.get_async_session") as mock_session:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_response
            mock_http_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_session.return_value = mock_client

            result = await get_my_stats()

            assert result["gamesPlayed"] == 100
            assert result["averageScore"] == 4500


class TestGameTools:
    """Tests for game-related tools."""

    @pytest.mark.asyncio
    async def test_get_game_details_success(self):
        """Test successful game details retrieval."""
        from server import get_game_details

        mock_response = {
            "token": "ABC123",
            "type": "standard",
            "map": {"name": "World"},
            "player": {
                "guesses": [
                    {"roundScoreInPoints": 5000, "distanceInMeters": 0},
                    {"roundScoreInPoints": 4500, "distanceInMeters": 100},
                ]
            }
        }

        with patch("server.get_async_session") as mock_session:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_response
            mock_http_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_session.return_value = mock_client

            result = await get_game_details("ABC123")

            assert result["token"] == "ABC123"
            assert result["map"]["name"] == "World"
            assert len(result["player"]["guesses"]) == 2


class TestAnalysisTools:
    """Tests for analysis tools."""

    @pytest.mark.asyncio
    async def test_analyze_recent_games_empty(self):
        """Test analysis with no games in feed."""
        from server import analyze_recent_games

        mock_feed_response = {"entries": []}

        with patch("server.get_async_session") as mock_session:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_feed_response
            mock_http_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_session.return_value = mock_client

            result = await analyze_recent_games(count=5)

            assert result["games_analyzed"] == 0
            assert result["total_score"] == 0
            assert result["games"] == []


class TestAuthentication:
    """Tests for authentication handling."""

    def test_get_ncfa_cookie_missing(self, monkeypatch):
        """Test error when cookie is not set."""
        monkeypatch.delenv("GEOGUESSR_NCFA_COOKIE", raising=False)

        from server import get_ncfa_cookie

        with pytest.raises(ValueError, match="GEOGUESSR_NCFA_COOKIE"):
            get_ncfa_cookie()

    def test_get_ncfa_cookie_present(self, monkeypatch):
        """Test cookie retrieval when set."""
        monkeypatch.setenv("GEOGUESSR_NCFA_COOKIE", "my_test_cookie")

        from server import get_ncfa_cookie

        cookie = get_ncfa_cookie()
        assert cookie == "my_test_cookie"


# Integration tests (marked to skip by default)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require a real GeoGuessr cookie."""

    @pytest.mark.asyncio
    async def test_real_profile_fetch(self):
        """Test fetching real profile data."""
        import os
        if not os.environ.get("GEOGUESSR_NCFA_COOKIE") or \
                os.environ.get("GEOGUESSR_NCFA_COOKIE") == "test_cookie_value":
            pytest.skip("Real NCFA cookie not configured")

        from server import get_my_profile

        result = await get_my_profile()
        assert "nick" in result
        assert "id" in result


if __name__ == "__main__":
    """Run tests automatically when script is executed directly."""
    import sys

    # Run pytest with verbose output and show print statements
    exit_code = pytest.main([
        __file__,
        "-v",  # Verbose output
        "-s",  # Show print statements
        "--tb=short",  # Shorter traceback format
        "-m", "not integration",  # Skip integration tests by default
    ])

    sys.exit(exit_code)