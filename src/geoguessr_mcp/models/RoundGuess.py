"""RoundGuess-related data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RoundGuess:
    """Represents a single round guess in a game."""

    round_number: int
    score: int
    distance_meters: float
    time_seconds: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    country: str = ""

    @classmethod
    def from_api_response(cls, data: dict, round_num: int = 0) -> "RoundGuess":
        """Create RoundGuess from API response."""
        return cls(
            round_number=round_num,
            score=data.get("roundScoreInPoints", data.get("score", 0)),
            distance_meters=data.get("distanceInMeters", data.get("distance", 0)),
            time_seconds=data.get("time", data.get("timeInSeconds", 0)),
            lat=data.get("lat", data.get("latitude")),
            lng=data.get("lng", data.get("longitude")),
            country=data.get("country", ""),
        )
