"""Achievement-related data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Achievement:
    """Represents a user achievement."""
    id: str
    name: str
    description: str = ""
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    progress: float = 0.0
    icon_url: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Achievement":
        """Create Achievement from API response."""
        return cls(
            id=data.get("id", data.get("achievementId", "")),
            name=data.get("name", data.get("title", "")),
            description=data.get("description", ""),
            unlocked=data.get("unlocked", data.get("achieved", False)),
            unlocked_at=data.get("unlockedAt", data.get("achievedAt")),
            progress=data.get("progress", 1.0 if data.get("unlocked") else 0.0),
            icon_url=data.get("icon", data.get("imageUrl")),
        )
