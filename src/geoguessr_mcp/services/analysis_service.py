"""Analysis and statistics calculations."""

from typing import List

from ..models.game import Game


class AnalysisService:
    """Service for analyzing game data."""

    @staticmethod
    def calculate_statistics(games: List[Game]) -> dict:
        """Calculate aggregate statistics from games."""
        if not games:
            return {"games_analyzed": 0, "total_score": 0, "average_score": 0, "perfect_rounds": 0}

        total_score = sum(g.total_score for g in games)
        total_rounds = sum(len(g.rounds) for g in games)
        perfect_rounds = sum(1 for g in games for r in g.rounds if r.score == 5000)

        return {
            "games_analyzed": len(games),
            "total_score": total_score,
            "average_score": total_score / len(games),
            "total_rounds": total_rounds,
            "perfect_rounds": perfect_rounds,
            "perfect_round_percentage": (
                (perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0
            ),
        }
