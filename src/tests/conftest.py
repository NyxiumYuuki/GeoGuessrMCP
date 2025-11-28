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
        "rating": {
            "rating": 1500,
            "deviation": 100
        }
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
                {"roundScoreInPoints": 4500, "distanceInMeters": 100, "time": 15},
            ]
        },
    }
