"""
Profile service for user data operations.

This service handles profile, stats, and achievement data with
dynamic schema adaptation.
"""

import logging

from ..api import DynamicResponse, Endpoints, GeoGuessrClient
from ..models import Achievement, UserProfile, UserStats

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile-related operations."""

    def __init__(self, client: GeoGuessrClient):
        self.client = client

    async def get_profile(
        self,
            session_token: str | None = None,
    ) -> tuple[UserProfile, DynamicResponse]:
        """
        Get current user's profile.

        Returns:
            Tuple of (UserProfile, DynamicResponse) for both structured and raw access
        """
        response = await self.client.get(Endpoints.PROFILES.GET_PROFILE, session_token)

        if response.is_success:
            profile = UserProfile.from_api_response(response.data)
            return profile, response

        raise ValueError(f"Failed to get profile: {response.data}")

    async def get_stats(
        self,
            session_token: str | None = None,
    ) -> tuple[UserStats, DynamicResponse]:
        """
        Get user statistics.

        Returns:
            Tuple of (UserStats, DynamicResponse)
        """
        response = await self.client.get(Endpoints.PROFILES.GET_STATS, session_token)

        if response.is_success:
            stats = UserStats.from_api_response(response.data)
            return stats, response

        raise ValueError(f"Failed to get stats: {response.data}")

    async def get_extended_stats(
        self,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """
        Get extended statistics.

        Returns raw DynamicResponse as extended stats have variable schema.
        """
        return await self.client.get(Endpoints.PROFILES.GET_EXTENDED_STATS, session_token)

    async def get_achievements(
        self,
            session_token: str | None = None,
    ) -> tuple[list[Achievement], DynamicResponse]:
        """
        Get user achievements.

        Returns:
            Tuple of (list of Achievement, DynamicResponse)
        """
        response = await self.client.get(Endpoints.PROFILES.GET_ACHIEVEMENTS, session_token)

        if response.is_success:
            achievements = []
            data = response.data

            # Handle different response formats
            if isinstance(data, list):
                achievements = [Achievement.from_api_response(a) for a in data]
            elif isinstance(data, dict) and "achievements" in data:
                achievements = [Achievement.from_api_response(a) for a in data["achievements"]]

            return achievements, response

        raise ValueError(f"Failed to get achievements: {response.data}")

    async def get_public_profile(
        self,
        user_id: str,
            session_token: str | None = None,
    ) -> tuple[UserProfile, DynamicResponse]:
        """Get another user's public profile."""
        endpoint = Endpoints.PROFILES.get_public_profile(user_id)
        response = await self.client.get(endpoint, session_token)

        if response.is_success:
            profile = UserProfile.from_api_response(response.data)
            return profile, response

        raise ValueError(f"Failed to get public profile: {response.data}")

    async def get_user_maps(
        self,
            session_token: str | None = None,
    ) -> DynamicResponse:
        """Get user's custom maps."""
        return await self.client.get(Endpoints.PROFILES.GET_USER_MAPS, session_token)

    async def get_comprehensive_profile(
        self,
            session_token: str | None = None,
    ) -> dict:
        """
        Get a comprehensive profile combining multiple endpoints.

        This method aggregates data from multiple sources and provides
        a unified view with schema information for the LLM.
        """
        results = {
            "profile": None,
            "stats": None,
            "extended_stats": None,
            "achievements": None,
            "schema_info": {},
            "errors": [],
        }

        # Get profile
        try:
            profile, response = await self.get_profile(session_token)
            results["profile"] = profile.to_dict()
            results["schema_info"]["profile"] = response.available_fields
        except Exception as e:
            results["errors"].append(f"Profile: {str(e)}")

        # Get stats
        try:
            stats, response = await self.get_stats(session_token)
            results["stats"] = stats.to_dict()
            results["schema_info"]["stats"] = response.available_fields
        except Exception as e:
            results["errors"].append(f"Stats: {str(e)}")

        # Get extended stats
        try:
            response = await self.get_extended_stats(session_token)
            if response.is_success:
                results["extended_stats"] = response.summarize()
                results["schema_info"]["extended_stats"] = response.available_fields
        except Exception as e:
            results["errors"].append(f"Extended stats: {str(e)}")

        # Get achievements summary
        try:
            achievements, response = await self.get_achievements(session_token)
            unlocked = [a for a in achievements if a.unlocked]
            results["achievements"] = {
                "total": len(achievements),
                "unlocked": len(unlocked),
                "recent": [
                    {"name": a.name, "unlocked_at": a.unlocked_at}
                    for a in sorted(unlocked, key=lambda x: x.unlocked_at or "", reverse=True)[:5]
                ],
            }
        except Exception as e:
            results["errors"].append(f"Achievements: {str(e)}")

        return results
