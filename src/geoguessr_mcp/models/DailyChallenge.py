"""DailyChallenge-related data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DailyChallenge:
    """Daily challenge information."""

    token: str
    map_name: str = ""
    date: str = ""
    time_limit: int = 0
    completed: bool = False
    score: Optional[int] = None
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "DailyChallenge":
        """Create DailyChallenge from API response."""
        return cls(
            token=data.get("token", data.get("challengeToken", "")),
            map_name=(
                data.get("map", {}).get("name", "") if isinstance(data.get("map"), dict) else ""
            ),
            date=data.get("date", data.get("day", "")),
            time_limit=data.get("timeLimit", 0),
            completed=data.get("completed", data.get("played", False)),
            score=data.get("score"),
            raw_data=data,
        )
