"""UserStats-related data models."""

from dataclasses import dataclass, field


@dataclass
class UserStats:
    """User statistics from various endpoints."""

    games_played: int = 0
    rounds_played: int = 0
    total_score: int = 0
    average_score: float = 0.0
    perfect_games: int = 0
    win_rate: float = 0.0
    streak_best: int = 0
    explorer_progress: float = 0.0
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "UserStats":
        """Create UserStats from API response with dynamic field mapping."""
        # Handle different response formats
        games = data.get("gamesPlayed", data.get("totalGames", data.get("games", 0)))
        rounds = data.get("roundsPlayed", data.get("totalRounds", 0))
        score = data.get("totalScore", data.get("score", 0))

        return cls(
            games_played=games,
            rounds_played=rounds,
            total_score=score,
            average_score=data.get("averageScore", score / games if games > 0 else 0),
            perfect_games=data.get("perfectGames", data.get("fiveKs", 0)),
            win_rate=data.get("winRate", data.get("winPercentage", 0.0)),
            streak_best=data.get("bestStreak", data.get("countryStreakBest", 0)),
            explorer_progress=data.get("explorerProgress", 0.0),
            raw_data=data,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "games_played": self.games_played,
            "rounds_played": self.rounds_played,
            "total_score": self.total_score,
            "average_score": round(self.average_score, 2),
            "perfect_games": self.perfect_games,
            "win_rate": round(self.win_rate, 4),
            "streak_best": self.streak_best,
            "explorer_progress": round(self.explorer_progress, 2),
        }
