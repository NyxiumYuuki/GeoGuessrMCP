"""
Profile-related business logic.
"""

from typing import Optional
from ..api.client import GeoguessrClient
from ..api.endpoints import Endpoints
from ..models.profile import UserProfile, UserStats


class ProfileService:
    """Service for profile operations."""

    def __init__(self, client: GeoguessrClient):
        """
        Initialize the profile service.

        Args:
            client: GeoGuessr API client
        """
        self.client = client

    async def get_profile(
        self,
        session_token: Optional[str] = None
    ) -> UserProfile:
        """
        Get user profile.

        Args:
            session_token: Optional session token for authentication

        Returns:
            UserProfile with user information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = await self.client.get(
            Endpoints.PROFILES.GET_PROFILE,
            session_token
        )
        data = response.json()
        return UserProfile.from_api_response(data)

    async def get_stats(
        self,
        session_token: Optional[str] = None
    ) -> UserStats:
        """
        Get user statistics.

        Args:
            session_token: Optional session token for authentication

        Returns:
            UserStats with user statistics

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = await self.client.get(
            Endpoints.PROFILES.GET_STATS,
            session_token
        )
        data = response.json()
        return UserStats.from_api_response(data)

    async def get_extended_stats(
        self,
        session_token: Optional[str] = None
    ) -> dict:
        """
        Get extended user statistics.

        Args:
            session_token: Optional session token for authentication

        Returns:
            Dictionary with extended statistics

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = await self.client.get(
            Endpoints.PROFILES.GET_EXTENDED_STATS,
            session_token
        )
        return response.json()

    async def get_achievements(
        self,
        session_token: Optional[str] = None
    ) -> list:
        """
        Get user achievements.

        Args:
            session_token: Optional session token for authentication

        Returns:
            List of achievement dictionaries

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = await self.client.get(
            Endpoints.PROFILES.GET_ACHIEVEMENTS,
            session_token
        )
        return response.json()

    async def get_public_profile(
        self,
        user_id: str,
        session_token: Optional[str] = None
    ) -> UserProfile:
        """
        Get public profile of another user.

        Args:
            user_id: User ID to fetch
            session_token: Optional session token for authentication

        Returns:
            UserProfile with public user information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = await self.client.get(
            Endpoints.PROFILES.get_public_profile(user_id),
            session_token
        )
        data = response.json()
        return UserProfile.from_api_response(data)
