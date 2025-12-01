"""
Analysis service for game statistics and strategy optimization.

This service provides comprehensive analysis capabilities with
dynamic data handling and LLM-friendly output formatting.
"""

import logging
from dataclasses import dataclass, field

from .game_service import GameService
from .profile_service import ProfileService
from ..api import GeoGuessrClient
from ..models import Game
from ..monitoring import schema_registry

logger = logging.getLogger(__name__)


@dataclass
class GameAnalysis:
    """Analysis results for a set of games."""

    games_analyzed: int = 0
    total_score: int = 0
    average_score: float = 0.0
    total_rounds: int = 0
    perfect_rounds: int = 0
    perfect_round_percentage: float = 0.0
    average_distance_meters: float = 0.0
    average_time_seconds: float = 0.0
    best_game_score: int = 0
    worst_game_score: int = 0
    score_trend: str = "stable"  # improving, declining, stable
    weak_areas: list = field(default_factory=list)
    strong_areas: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "games_analyzed": self.games_analyzed,
            "total_score": self.total_score,
            "average_score": round(self.average_score, 2),
            "total_rounds": self.total_rounds,
            "perfect_rounds": self.perfect_rounds,
            "perfect_round_percentage": round(self.perfect_round_percentage, 2),
            "average_distance_meters": round(self.average_distance_meters, 2),
            "average_time_seconds": round(self.average_time_seconds, 2),
            "best_game_score": self.best_game_score,
            "worst_game_score": self.worst_game_score,
            "score_trend": self.score_trend,
            "weak_areas": self.weak_areas,
            "strong_areas": self.strong_areas,
        }


class AnalysisService:
    """Service for game analysis and strategy optimization."""

    def __init__(
        self,
        client: GeoGuessrClient,
            game_service: GameService | None = None,
            profile_service: ProfileService | None = None,
    ):
        self.client = client
        self.game_service = game_service or GameService(client)
        self.profile_service = profile_service or ProfileService(client)

    @staticmethod
    def analyze_games(games: list[Game]) -> GameAnalysis:
        """
        Analyze a list of games and calculate statistics.

        Args:
            games: List of Game objects to analyze

        Returns:
            GameAnalysis with computed statistics
        """
        if not games:
            return GameAnalysis()

        total_score = sum(g.total_score for g in games)
        all_rounds = [r for g in games for r in g.rounds]
        total_rounds = len(all_rounds)
        perfect_rounds = sum(1 for r in all_rounds if r.score == 5000)

        # Calculate averages
        avg_distance = (
            sum(r.distance_meters for r in all_rounds) / total_rounds if total_rounds > 0 else 0
        )
        avg_time = sum(r.time_seconds for r in all_rounds) / total_rounds if total_rounds > 0 else 0

        # Find best and worst
        scores = [g.total_score for g in games]
        best_score = max(scores) if scores else 0
        worst_score = min(scores) if scores else 0

        # Determine trend (simple moving average comparison)
        trend = "stable"
        if len(games) >= 4:
            first_half = sum(g.total_score for g in games[: len(games) // 2]) / (len(games) // 2)
            second_half = sum(g.total_score for g in games[len(games) // 2 :]) / (
                len(games) - len(games) // 2
            )
            if second_half > first_half * 1.05:
                trend = "improving"
            elif second_half < first_half * 0.95:
                trend = "declining"

        # Identify weak/strong areas based on scores
        weak_areas = []
        strong_areas = []

        for game in games:
            for round_guess in game.rounds:
                if round_guess.score < 2000:
                    weak_areas.append(
                        {
                            "game": game.token,
                            "round": round_guess.round_number,
                            "score": round_guess.score,
                            "distance": round_guess.distance_meters,
                        }
                    )
                elif round_guess.score >= 4500:
                    strong_areas.append(
                        {
                            "game": game.token,
                            "round": round_guess.round_number,
                            "score": round_guess.score,
                        }
                    )

        return GameAnalysis(
            games_analyzed=len(games),
            total_score=total_score,
            average_score=total_score / len(games),
            total_rounds=total_rounds,
            perfect_rounds=perfect_rounds,
            perfect_round_percentage=(
                (perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0
            ),
            average_distance_meters=avg_distance,
            average_time_seconds=avg_time,
            best_game_score=best_score,
            worst_game_score=worst_score,
            score_trend=trend,
            weak_areas=weak_areas[:10],  # Limit to 10
            strong_areas=strong_areas[:10],
        )

    async def analyze_recent_games(
        self,
        count: int = 10,
            session_token: str | None = None,
    ) -> dict:
        """
        Analyze recent games and provide statistics summary.

        Args:
            count: Number of recent games to analyze
            session_token: Optional session token

        Returns:
            Dictionary with analysis results and raw game data
        """
        games = await self.game_service.get_recent_games(count, session_token)
        analysis = self.analyze_games(games)

        return {
            "analysis": analysis.to_dict(),
            "games": [g.to_dict() for g in games],
            "schema_info": {
                "endpoints_used": ["/v4/feed/private", "/v3/games/{token}"],
                "available_schemas": schema_registry.get_available_endpoints(),
            },
        }

    async def get_performance_summary(
        self,
            session_token: str | None = None,
    ) -> dict:
        """
        Get a comprehensive performance summary.

        Combines profile stats, achievements, season info, and recent game analysis.
        """
        results = {
            "profile": None,
            "stats": None,
            "season": None,
            "recent_games_analysis": None,
            "explorer": None,
            "objectives": None,
            "api_status": schema_registry.get_schema_summary(),
            "errors": [],
        }

        # Get comprehensive profile
        try:
            results["profile"] = await self.profile_service.get_comprehensive_profile(session_token)
        except Exception as e:
            results["errors"].append(f"Profile: {str(e)}")

        # Get season stats
        try:
            stats, response = await self.game_service.get_season_stats(session_token)
            results["season"] = {
                "data": {
                    "rank": stats.rank,
                    "rating": stats.rating,
                    "games_played": stats.games_played,
                    "division": stats.division,
                },
                "raw_fields": response.available_fields,
            }
        except Exception as e:
            results["errors"].append(f"Season: {str(e)}")

        # Analyze recent games
        try:
            results["recent_games_analysis"] = await self.analyze_recent_games(5, session_token)
        except Exception as e:
            results["errors"].append(f"Recent games: {str(e)}")

        # Get explorer progress
        try:
            response = await self.client.get(self._create_endpoint("/v3/explorer"), session_token)
            if response.is_success:
                results["explorer"] = response.summarize()
        except Exception as e:
            results["errors"].append(f"Explorer: {str(e)}")

        # Get objectives
        try:
            response = await self.client.get(self._create_endpoint("/v4/objectives"), session_token)
            if response.is_success:
                results["objectives"] = response.summarize()
        except Exception as e:
            results["errors"].append(f"Objectives: {str(e)}")

        return results

    async def get_strategy_recommendations(
        self,
            session_token: str | None = None,
    ) -> dict:
        """
        Generate strategy recommendations based on performance analysis.

        This method analyzes the user's gameplay patterns and provides
        actionable recommendations for improvement.
        """
        # Get recent games for analysis
        games = await self.game_service.get_recent_games(20, session_token)
        analysis = self.analyze_games(games)

        recommendations = []

        # Analyze perfect round rate
        if analysis.perfect_round_percentage < 20:
            recommendations.append(
                {
                    "category": "accuracy",
                    "priority": "high",
                    "recommendation": "Focus on improving pinpoint accuracy",
                    "detail": f"Your perfect round rate is {analysis.perfect_round_percentage:.1f}%. "
                    "Practice with familiar maps to build confidence.",
                }
            )

        # Analyze time usage
        if analysis.average_time_seconds < 30:
            recommendations.append(
                {
                    "category": "time_management",
                    "priority": "medium",
                    "recommendation": "Consider taking more time per round",
                    "detail": f"Average time: {analysis.average_time_seconds:.0f}s. "
                    "Taking a bit more time can improve accuracy.",
                }
            )

        # Analyze score trend
        if analysis.score_trend == "declining":
            recommendations.append(
                {
                    "category": "consistency",
                    "priority": "high",
                    "recommendation": "Your scores are trending downward",
                    "detail": "Consider taking breaks and reviewing your weak areas.",
                }
            )

        # Check for weak areas pattern
        if len(analysis.weak_areas) > 5:
            recommendations.append(
                {
                    "category": "practice",
                    "priority": "medium",
                    "recommendation": "Practice specific regions",
                    "detail": f"You had {len(analysis.weak_areas)} rounds under 2000 points. "
                    "Consider using region-specific practice maps.",
                }
            )

        return {
            "analysis_summary": {
                "games_analyzed": analysis.games_analyzed,
                "average_score": round(analysis.average_score, 0),
                "trend": analysis.score_trend,
                "perfect_rate": f"{analysis.perfect_round_percentage:.1f}%",
            },
            "recommendations": recommendations,
            "data_sources": {
                "endpoints_used": schema_registry.get_available_endpoints(),
                "last_updated": schema_registry.get_schema_summary()
                .get("endpoints", {})
                .get("/v4/feed/private", {})
                .get("last_updated"),
            },
        }

    @staticmethod
    def _create_endpoint(path: str):
        """Create simple endpoint info for raw requests."""
        from ..api.endpoints import EndpointInfo

        return EndpointInfo(path=path, description=f"Request to {path}")
