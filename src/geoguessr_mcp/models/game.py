"""Game-related data models."""

from dataclasses import dataclass
from typing import List


@dataclass
class RoundGuess:
    """Represents a single round guess."""

    score: int
    distance_meters: int
    time_seconds: int


@dataclass
class Game:
    """Represents a complete game."""

    token: str
    map_name: str
    mode: str
    total_score: int
    rounds: List[RoundGuess]

    @classmethod
    def from_api_response(cls, data: dict) -> "Game":
        """Create Game from API response."""
        rounds = [
            RoundGuess(
                score=r.get("roundScoreInPoints", 0),
                distance_meters=r.get("distanceInMeters", 0),
                time_seconds=r.get("time", 0),
            )
            for r in data.get("player", {}).get("guesses", [])
        ]

        return cls(
            token=data["token"],
            map_name=data.get("map", {}).get("name", "Unknown"),
            mode=data.get("type", "Unknown"),
            total_score=sum(r.score for r in rounds),
            rounds=rounds,
        )
