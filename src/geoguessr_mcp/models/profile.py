"""Profile-related data models."""

from dataclasses import dataclass


@dataclass
class UserProfile:
    """User profile information."""

    id: str
    nick: str
    email: str
    country: str
    level: int
    created: str
    is_verified: bool

    @classmethod
    def from_api_response(cls, data: dict) -> "UserProfile":
        """Create UserProfile from API response."""
        return cls(
            id=data["id"],
            nick=data["nick"],
            email=data.get("email", ""),
            country=data.get("country", ""),
            level=data.get("level", 0),
            created=data.get("created", ""),
            is_verified=data.get("isVerified", False),
        )
