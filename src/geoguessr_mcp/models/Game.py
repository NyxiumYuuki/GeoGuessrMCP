"""Game-related data models."""

from dataclasses import dataclass, field
from typing import Optional

from .RoundGuess import RoundGuess


@dataclass
class Game:
    """Represents a complete game."""

    token: str
    map_name: str
    mode: str
    total_score: int
    rounds: list[RoundGuess] = field(default_factory=list)
    created_at: Optional[str] = None
    finished: bool = False
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "Game":
        """Create Game from API response."""
        rounds = []
        guesses = data.get("player", {}).get("guesses", [])
        if not guesses:
            guesses = data.get("rounds", data.get("guesses", []))

        for i, guess_data in enumerate(guesses):
            rounds.append(RoundGuess.from_api_response(guess_data, i + 1))

        map_data = data.get("map", {})
        map_name = map_data.get("name", "Unknown") if isinstance(map_data, dict) else str(map_data)

        return cls(
            token=data.get("token", data.get("gameToken", data.get("id", ""))),
            map_name=map_name,
            mode=data.get("type", data.get("gameType", data.get("mode", "Unknown"))),
            total_score=sum(r.score for r in rounds),
            rounds=rounds,
            created_at=data.get("created", data.get("createdAt")),
            finished=data.get("state") == "finished" or data.get("finished", False),
            raw_data=data,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "token": self.token,
            "map_name": self.map_name,
            "mode": self.mode,
            "total_score": self.total_score,
            "rounds": [
                {
                    "round": r.round_number,
                    "score": r.score,
                    "distance_m": round(r.distance_meters, 1),
                    "time_s": r.time_seconds,
                }
                for r in self.rounds
            ],
            "finished": self.finished,
        }
