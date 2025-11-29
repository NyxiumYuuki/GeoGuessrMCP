"""Shared test fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from geoguessr_mcp.api.dynamic_response import DynamicResponse
from geoguessr_mcp.models import RoundGuess, Game
from geoguessr_mcp.services import AnalysisService, GameService, ProfileService


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("GEOGUESSR_NCFA_COOKIE", "test_cookie_value")


@pytest.fixture
def mock_client():
    """Create a mock GeoGuessrClient."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def mock_session():
    """Create a mock async HTTP session."""
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    return mock_client


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
    """Create a mock DynamicResponse factory."""

    def create_response(data, success=True, status_code=200):
        response = MagicMock(spec=DynamicResponse)
        response.data = data
        response.is_success = success
        response.status_code = status_code
        response.available_fields = list(data.keys()) if isinstance(data, dict) else []
        response.summarize.return_value = {"data_summary": data}
        return response

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
