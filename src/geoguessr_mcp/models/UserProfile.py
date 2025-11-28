"""UserProfile-related data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    """User profile information."""
    id: str
    nick: str
    email: str = ""
    country: str = ""
    level: int = 0
    created: str = ""
    is_verified: bool = False
    is_pro: bool = False
    avatar_url: Optional[str] = None
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "UserProfile":
        """Create UserProfile from API response with dynamic field mapping."""
        return cls(
            id=data.get("id", ""),
            nick=data.get("nick", data.get("username", "")),
            email=data.get("email", ""),
            country=data.get("country", data.get("countryCode", "")),
            level=data.get("level", data.get("xpLevel", 0)),
            created=data.get("created", data.get("createdAt", "")),
            is_verified=data.get("isVerified", data.get("verified", False)),
            is_pro=data.get("isPro", data.get("isProUser", False)),
            avatar_url=data.get("pin", {}).get("url") if isinstance(data.get("pin"), dict) else None,
            raw_data=data,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "nick": self.nick,
            "email": self.email,
            "country": self.country,
            "level": self.level,
            "created": self.created,
            "is_verified": self.is_verified,
            "is_pro": self.is_pro,
            "avatar_url": self.avatar_url,
        }
