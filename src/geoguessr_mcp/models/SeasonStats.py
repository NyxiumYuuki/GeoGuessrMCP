"""SeasonStats-related data models."""

from dataclasses import dataclass, field


@dataclass
class SeasonStats:
    """Competitive season statistics."""

    season_id: str
    season_name: str = ""
    rank: int = 0
    rating: int = 0
    games_played: int = 0
    wins: int = 0
    division: str = ""
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "SeasonStats":
        """Create SeasonStats from API response."""
        return cls(
            season_id=data.get("seasonId", data.get("id", "")),
            season_name=data.get("seasonName", data.get("name", "")),
            rank=data.get("rank", data.get("position", 0)),
            rating=data.get("rating", data.get("elo", data.get("score", 0))),
            games_played=data.get("gamesPlayed", data.get("games", 0)),
            wins=data.get("wins", 0),
            division=data.get("division", data.get("tier", "")),
            raw_data=data,
        )
