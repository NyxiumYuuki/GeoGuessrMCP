"""
This module contains unit tests for classes and services provided in the
`geoguessr_mcp` library. It includes test cases for analyzing games,
evaluating statistical trends, and extracting detailed insights from
game performance data.
"""

from unittest.mock import patch

import pytest

from geoguessr_mcp.models import Game, RoundGuess
from geoguessr_mcp.services.analysis_service import AnalysisService, GameAnalysis


class TestGameAnalysis:
    """Tests for GameAnalysis dataclass."""

    def test_default_values(self):
        """Test GameAnalysis default values."""
        analysis = GameAnalysis()

        assert analysis.games_analyzed == 0
        assert analysis.total_score == 0
        assert analysis.average_score == 0.0
        assert analysis.perfect_round_percentage == 0.0
        assert analysis.score_trend == "stable"
        assert analysis.weak_areas == []
        assert analysis.strong_areas == []

    def test_to_dict(self):
        """Test GameAnalysis to_dict method."""
        analysis = GameAnalysis(
            games_analyzed=10,
            total_score=200000,
            average_score=20000.5,
            total_rounds=50,
            perfect_rounds=15,
            perfect_round_percentage=30.0,
            average_distance_meters=500.123,
            average_time_seconds=45.678,
            best_game_score=25000,
            worst_game_score=15000,
            score_trend="improving",
        )

        result = analysis.to_dict()

        assert result["games_analyzed"] == 10
        assert result["average_score"] == 20000.5
        assert result["perfect_round_percentage"] == 30.0
        assert result["score_trend"] == "improving"


class TestAnalysisService:
    """Tests for AnalysisService."""

    def test_analyze_games_empty(self):
        """Test analyzing empty game list."""
        result = AnalysisService.analyze_games([])

        assert result.games_analyzed == 0
        assert result.total_score == 0
        assert result.average_score == 0.0

    def test_analyze_games_single_game(self):
        """Test analyzing single game."""
        rounds = [
            RoundGuess(round_number=1, score=5000, distance_meters=0, time_seconds=20),
            RoundGuess(round_number=2, score=4500, distance_meters=100, time_seconds=25),
            RoundGuess(round_number=3, score=4000, distance_meters=200, time_seconds=30),
        ]
        game = Game(
            token="test-game",
            map_name="World",
            mode="standard",
            total_score=13500,
            rounds=rounds,
            finished=True,
        )

        result = AnalysisService.analyze_games([game])

        assert result.games_analyzed == 1
        assert result.total_score == 13500
        assert result.average_score == 13500
        assert result.total_rounds == 3
        assert result.perfect_rounds == 1
        assert result.perfect_round_percentage == pytest.approx(33.33, rel=0.01)

    def test_analyze_games_multiple_games(self, sample_games):
        """Test analyzing multiple games."""
        result = AnalysisService.analyze_games(sample_games)

        assert result.games_analyzed == 5
        assert result.total_rounds == 25
        assert result.average_score == result.total_score / 5
        assert result.best_game_score >= result.worst_game_score

    def test_analyze_games_trend_improving(self):
        """Test score trend detection - improving."""
        # Create games with improving scores
        games = []
        for i in range(6):
            base_score = 15000 + (i * 2000)  # Increasing scores
            rounds = [RoundGuess(round_number=1, score=base_score, distance_meters=100, time_seconds=30)]
            game = Game(
                token=f"game-{i}",
                map_name="World",
                mode="standard",
                total_score=base_score,
                rounds=rounds,
                finished=True,
            )
            games.append(game)

        result = AnalysisService.analyze_games(games)

        assert result.score_trend == "improving"

    def test_analyze_games_trend_declining(self):
        """Test score trend detection - declining."""
        # Create games with declining scores
        games = []
        for i in range(6):
            base_score = 25000 - (i * 2000)  # Decreasing scores
            rounds = [RoundGuess(round_number=1, score=base_score, distance_meters=100, time_seconds=30)]
            game = Game(
                token=f"game-{i}",
                map_name="World",
                mode="standard",
                total_score=base_score,
                rounds=rounds,
                finished=True,
            )
            games.append(game)

        result = AnalysisService.analyze_games(games)

        assert result.score_trend == "declining"

    def test_analyze_games_weak_areas(self):
        """Test weak areas' identification."""
        rounds = [
            RoundGuess(round_number=1, score=5000, distance_meters=0, time_seconds=20),
            RoundGuess(round_number=2, score=1500, distance_meters=5000, time_seconds=60),  # Weak
            RoundGuess(round_number=3, score=1000, distance_meters=8000, time_seconds=90),  # Weak
        ]
        game = Game(
            token="test-game",
            map_name="World",
            mode="standard",
            total_score=7500,
            rounds=rounds,
            finished=True,
        )

        result = AnalysisService.analyze_games([game])

        assert len(result.weak_areas) == 2
        assert all(area["score"] < 2000 for area in result.weak_areas)

    def test_analyze_games_strong_areas(self):
        """Test strong areas' identification."""
        rounds = [
            RoundGuess(round_number=1, score=5000, distance_meters=0, time_seconds=20),
            RoundGuess(round_number=2, score=4800, distance_meters=50, time_seconds=25),
            RoundGuess(round_number=3, score=2000, distance_meters=500, time_seconds=30),
        ]
        game = Game(
            token="test-game",
            map_name="World",
            mode="standard",
            total_score=11800,
            rounds=rounds,
            finished=True,
        )

        result = AnalysisService.analyze_games([game])

        assert len(result.strong_areas) == 2
        assert all(area["score"] >= 4500 for area in result.strong_areas)

    @pytest.mark.asyncio
    async def test_analyze_recent_games(
            self, analysis_service, mock_game_service, sample_games
    ):
        """Test analyze_recent_games method."""
        mock_game_service.get_recent_games.return_value = sample_games

        with patch.object(
                analysis_service,
                'analyze_games',
                wraps=AnalysisService.analyze_games
        ):
            result = await analysis_service.analyze_recent_games(count=5)

        assert "analysis" in result
        assert "games" in result
        assert result["analysis"]["games_analyzed"] == 5
        mock_game_service.get_recent_games.assert_called_once_with(5, None)

    @pytest.mark.asyncio
    async def test_analyze_recent_games_with_session(
            self, analysis_service, mock_game_service, sample_games
    ):
        """Test analyze_recent_games with session token."""
        mock_game_service.get_recent_games.return_value = sample_games

        await analysis_service.analyze_recent_games(
            count=10,
            session_token="test_token"
        )

        mock_game_service.get_recent_games.assert_called_once_with(10, "test_token")

    @pytest.mark.asyncio
    async def test_get_performance_summary(
            self, analysis_service, mock_game_service, mock_profile_service,
            mock_client, sample_games, mock_season_stats_data, mock_dynamic_response
    ):
        """Test comprehensive performance summary."""
        mock_profile_service.get_comprehensive_profile.return_value = {
            "profile": {"nick": "TestPlayer"},
            "stats": {"games_played": 100},
        }

        mock_season_response = mock_dynamic_response(mock_season_stats_data)
        from geoguessr_mcp.models import SeasonStats
        mock_season_stats = SeasonStats.from_api_response(mock_season_stats_data)
        mock_game_service.get_season_stats.return_value = (mock_season_stats, mock_season_response)
        mock_game_service.get_recent_games.return_value = sample_games[:3]

        mock_client.get.return_value = mock_dynamic_response({"progress": 0.5})

        result = await analysis_service.get_performance_summary()

        assert result["profile"] is not None
        assert result["season"] is not None
        assert result["recent_games_analysis"] is not None
        assert "api_status" in result

    @pytest.mark.asyncio
    async def test_get_performance_summary_with_errors(
            self, analysis_service, mock_game_service, mock_profile_service, mock_client
    ):
        """Test performance summary handles errors gracefully."""
        mock_profile_service.get_comprehensive_profile.side_effect = Exception("Profile error")
        mock_game_service.get_season_stats.side_effect = Exception("Season error")
        mock_game_service.get_recent_games.return_value = []
        mock_client.get.side_effect = Exception("API error")

        result = await analysis_service.get_performance_summary()

        assert len(result["errors"]) > 0
        assert result["profile"] is None
        assert result["season"] is None

    @pytest.mark.asyncio
    async def test_get_strategy_recommendations_low_perfect_rate(
            self, analysis_service, mock_game_service
    ):
        """Test strategy recommendations for low perfect round rate."""
        # Create games with no perfect rounds
        rounds = [
            RoundGuess(round_number=i, score=3000, distance_meters=500, time_seconds=30)
            for i in range(5)
        ]
        games = [
            Game(token="g1", map_name="World", mode="standard", total_score=15000, rounds=rounds, finished=True)
            for _ in range(5)
        ]
        mock_game_service.get_recent_games.return_value = games

        result = await analysis_service.get_strategy_recommendations()

        assert len(result["recommendations"]) > 0
        accuracy_recs = [r for r in result["recommendations"] if r["category"] == "accuracy"]
        assert len(accuracy_recs) > 0

    @pytest.mark.asyncio
    async def test_get_strategy_recommendations_fast_play(
            self, analysis_service, mock_game_service
    ):
        """Test strategy recommendations for fast play style."""
        # Create games with very short time
        rounds = [
            RoundGuess(round_number=i, score=3500, distance_meters=300, time_seconds=15)
            for i in range(5)
        ]
        games = [
            Game(token="g1", map_name="World", mode="standard", total_score=17500, rounds=rounds, finished=True)
            for _ in range(5)
        ]
        mock_game_service.get_recent_games.return_value = games

        result = await analysis_service.get_strategy_recommendations()

        time_recs = [r for r in result["recommendations"] if r["category"] == "time_management"]
        assert len(time_recs) > 0

    @pytest.mark.asyncio
    async def test_get_strategy_recommendations_declining_trend(
            self, analysis_service, mock_game_service
    ):
        """Test strategy recommendations for declining performance."""
        # Create games with declining scores
        games = []
        for i in range(6):
            base_score = 25000 - (i * 3000)
            rounds = [RoundGuess(round_number=1, score=base_score, distance_meters=100, time_seconds=45)]
            game = Game(
                token=f"game-{i}",
                map_name="World",
                mode="standard",
                total_score=base_score,
                rounds=rounds,
                finished=True,
            )
            games.append(game)
        mock_game_service.get_recent_games.return_value = games

        result = await analysis_service.get_strategy_recommendations()

        consistency_recs = [r for r in result["recommendations"] if r["category"] == "consistency"]
        assert len(consistency_recs) > 0
        assert result["analysis_summary"]["trend"] == "declining"

    @pytest.mark.asyncio
    async def test_get_strategy_recommendations_many_weak_areas(
            self, analysis_service, mock_game_service
    ):
        """Test strategy recommendations for many weak rounds."""
        # Create games with many low scores
        games = []
        for i in range(4):
            rounds = [
                RoundGuess(round_number=j, score=1500, distance_meters=5000, time_seconds=60)
                for j in range(5)
            ]
            game = Game(
                token=f"game-{i}",
                map_name="World",
                mode="standard",
                total_score=7500,
                rounds=rounds,
                finished=True,
            )
            games.append(game)
        mock_game_service.get_recent_games.return_value = games

        result = await analysis_service.get_strategy_recommendations()

        practice_recs = [r for r in result["recommendations"] if r["category"] == "practice"]
        assert len(practice_recs) > 0
