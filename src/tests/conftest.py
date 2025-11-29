"""Shared test fixtures."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("GEOGUESSR_NCFA_COOKIE", "test_cookie_value")


@pytest.fixture
def mock_session():
    """Create a mock async HTTP session."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    return mock_client


@pytest.fixture
def mock_profile_data():
    """Standard profile response data."""
    return {
        "id": "test-user-id",
        "nick": "TestPlayer",
        "email": "test@example.com",
        "country": "FR",
        "created": "2025-01-01T00:00:00.000Z",
        "isVerified": True,
        "level": 50,
        "rating": {"rating": 1500, "deviation": 100},
        "isProUser": True,
    }


@pytest.fixture
def mock_game_data():
    """Standard game response data."""
    return {
        "token": "ABC123",
        "type": "standard",
        "map": {"name": "World"},
        "player": {
            "guesses": [
                {"roundScoreInPoints": 5000, "distanceInMeters": 0, "time": 10},
                {"roundScoreInPoints": 4500, "distanceInMeters": 120, "time": 15},
                {"roundScoreInPoints": 3800, "distanceInMeters": 100, "time": 20},
                {"roundScoreInPoints": 4900, "distanceInMeters": 100, "time": 25},
                {"roundScoreInPoints": 5000, "distanceInMeters": 100, "time": 35},
            ]
        },
        "state": "finished",
    }


@pytest.fixture
def mock_stats_data():
    """Standard user stats response data."""
    return {
        "games": 100,
        "totalRounds": 500,
        "score": 2250000,
        "perfectGames": 10,
        "winRate": 0.65,
        "bestStreak": 25,
    }


@pytest.fixture
def mock_season_stats_data():
    """Standard season stats response data."""
    return {
        "id": "season-2024-1",
        "name": "Season 1 2024",
        "position": 150,
        "elo": 1850,
        "games": 45,
        "wins": 30,
        "tier": "Gold",
    }
