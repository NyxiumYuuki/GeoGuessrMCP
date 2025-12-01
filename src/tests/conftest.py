"""Shared test fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geoguessr_mcp.api import GeoGuessrClient
from geoguessr_mcp.api.dynamic_response import DynamicResponse
from geoguessr_mcp.auth import SessionManager, UserSession
from geoguessr_mcp.config import settings
from geoguessr_mcp.models import Game, RoundGuess
from geoguessr_mcp.services import AnalysisService, GameService, ProfileService


@pytest.fixture(autouse=True)
def mock_env(request, monkeypatch):
    """Set up environment variables for testing."""
    # Skip this fixture if the test has the 'real_env' marker
    if "real_env" in request.keywords:
        yield
        return

    # Clear the default cookie in settings to avoid interference
    monkeypatch.setattr(settings, "DEFAULT_NCFA_COOKIE", None)

    # Clear schema registry to avoid interference from registered schemas
    from geoguessr_mcp.monitoring.schema.schema_registry import schema_registry

    # Store original schemas
    original_schemas = schema_registry.schemas.copy()
    # Clear all schemas for testing
    schema_registry.schemas.clear()

    # Ensure required settings are set
    if not hasattr(settings, "GEOGUESSR_API_URL") or not settings.GEOGUESSR_API_URL:
        monkeypatch.setattr(settings, "GEOGUESSR_API_URL", "https://api.geoguessr.com")
    if not hasattr(settings, "GEOGUESSR_DOMAIN_NAME") or not settings.GEOGUESSR_DOMAIN_NAME:
        monkeypatch.setattr(settings, "GEOGUESSR_DOMAIN_NAME", ".geoguessr.com")

    # Restore schemas after test
    yield
    schema_registry._schemas = original_schemas


@pytest.fixture
def mock_client():
    """Create a mock GeoGuessrClient."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def real_client():
    """Create a real client with environment authentication."""
    real_cookie = os.getenv("GEOGUESSR_NCFA_COOKIE")
    session_manager = SessionManager(default_cookie=real_cookie)
    return GeoGuessrClient(session_manager)


@pytest.fixture
def client(mock_session_manager):
    """Create a GeoGuessrClient with mocked session manager."""
    return GeoGuessrClient(mock_session_manager)


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = MagicMock(spec=SessionManager)
    manager.get_session = AsyncMock(
        return_value=UserSession(
            ncfa_cookie="test_cookie",
            user_id="test-user",
            username="TestUser",
            email="test@example.com",
        )
    )
    return manager


@pytest.fixture
def mock_session():
    """Create a mock async HTTP session."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    return mock_client


@pytest.fixture
def session_manager():
    """Create a SessionManager without default cookie."""
    return SessionManager(default_cookie=None)


@pytest.fixture
def session_manager_with_default():
    """Create a SessionManager with a default cookie."""
    return SessionManager(default_cookie="test_cookie_value")


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for testing."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_game_service():
    """Create a mock GameService."""
    service = MagicMock()
    service.get_recent_games = AsyncMock()
    service.get_season_stats = AsyncMock()
    return service


@pytest.fixture
def mock_profile_service():
    """Create a mock ProfileService."""
    service = MagicMock()
    service.get_comprehensive_profile = AsyncMock()
    return service


@pytest.fixture
def analysis_service(mock_client, mock_game_service, mock_profile_service):
    """Create AnalysisService with mocked dependencies."""
    return AnalysisService(
        mock_client,
        game_service=mock_game_service,
        profile_service=mock_profile_service,
    )


@pytest.fixture
def game_service(mock_client):
    """Create GameService with mocked client."""
    return GameService(mock_client)


@pytest.fixture
def profile_service(mock_client):
    """Create ProfileService with mocked client."""
    return ProfileService(mock_client)


@pytest.fixture
def mock_dynamic_response():
    """Create a DynamicResponse factory for testing."""

    def create_response(data, success=True, status_code=200, endpoint="/mock/endpoint"):
        """Create a real DynamicResponse instance for testing.
        :param data:
        :param status_code:
        :param endpoint:
        :type success: object
        """
        return DynamicResponse(
            data=data,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=100.0,
        )

    return create_response


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


@pytest.fixture
def mock_activity_feed_data():
    """Activity feed response data."""
    return {
        "entries": [
            {
                "type": "PlayedGame",
                "payload": {"gameToken": "game-token-1"},
                "timestamp": "2024-01-15T10:00:00Z",
            },
            {
                "type": "PlayedGame",
                "payload": {"gameToken": "game-token-2"},
                "timestamp": "2024-01-14T10:00:00Z",
            },
            {
                "type": "Achievement",
                "payload": {"achievementId": "ach-1"},
                "timestamp": "2024-01-13T10:00:00Z",
            },
        ]
    }


@pytest.fixture
def sample_games():
    """Create sample Game objects for testing."""
    games = []
    for i in range(5):
        rounds = [
            RoundGuess(
                round_number=j + 1,
                score=5000 - (i * 200) - (j * 100),  # Varying scores
                distance_meters=100.0 * (i + 1),
                time_seconds=30 + i * 5,
            )
            for j in range(5)
        ]
        game = Game(
            token=f"game-{i}",
            map_name="World",
            mode="standard",
            total_score=sum(r.score for r in rounds),
            rounds=rounds,
            finished=True,
        )
        games.append(game)
    return games
