"""
User context for multi-user support.

This module provides the UserContext class that tracks which user
is making a request and their associated GeoGuessr session.
"""

from dataclasses import dataclass
from typing import Optional

from .session import UserSession


@dataclass
class UserContext:
    """
    Context for a specific user making a request.

    This class is attached to each request and contains information
    about the authenticated user and their GeoGuessr session.
    """

    api_key: str
    """The API key used to authenticate this request"""

    session: Optional[UserSession] = None
    """The GeoGuessr session for this user (if logged in)"""

    @property
    def user_id(self) -> str:
        """Get the user ID for this context."""
        if self.session:
            return self.session.user_id
        return f"anonymous_{hash(self.api_key) % 10000:04d}"

    @property
    def username(self) -> str:
        """Get the username for this context."""
        if self.session:
            return self.session.username
        return f"User-{hash(self.api_key) % 10000:04d}"

    @property
    def ncfa_cookie(self) -> Optional[str]:
        """Get the NCFA cookie for this user."""
        if self.session:
            return self.session.ncfa_cookie
        return None

    @property
    def is_authenticated(self) -> bool:
        """Check if this user has a valid GeoGuessr session."""
        return self.session is not None and self.session.is_valid()

    def __repr__(self) -> str:
        """String representation of user context."""
        auth_status = "authenticated" if self.is_authenticated else "not authenticated"
        return f"UserContext(user_id={self.user_id}, {auth_status})"
