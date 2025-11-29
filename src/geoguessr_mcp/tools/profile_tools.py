"""
This module defines the `register_profile_tools` function, which registers a
suite of profile-related functionalities as tools in a FastMCP application.

It includes tools for retrieving user profile data, game statistics, achievements,
and other related functionality. These tools are dynamically registered with an
instance of FastMCP, allowing the client to interact with profile and game meta-data.

The tools are designed to handle asynchronous operations and adapt to changes
from the underlying service API. Tools return structured data for easy consumption.
"""

from mcp.server.fastmcp import FastMCP

from .auth_tools import get_current_session_token
from ..services.profile_service import ProfileService


def register_profile_tools(mcp: FastMCP, profile_service: ProfileService):
    """Register profile-related tools."""

    @mcp.tool()
    async def get_my_profile() -> dict:
        """
        Get the current user's profile information.

        Returns profile data including username, level, country, and more.
        The response format adapts to API changes automatically.
        """
        session_token = get_current_session_token()
        profile, response = await profile_service.get_profile(session_token)

        return {
            "profile": profile.to_dict(),
            "available_fields": response.available_fields,
            "raw_data_preview": response.summarize(max_depth=1),
        }

    @mcp.tool()
    async def get_my_stats() -> dict:
        """
        Get the current user's game statistics.

        Returns statistics like games played, average score, win rate, etc.
        """
        session_token = get_current_session_token()
        stats, response = await profile_service.get_stats(session_token)

        return {
            "stats": stats.to_dict(),
            "available_fields": response.available_fields,
        }

    @mcp.tool()
    async def get_extended_stats() -> dict:
        """
        Get extended statistics not shown on the profile page.

        Returns additional metrics and detailed breakdowns.
        Response format is dynamic - check available_fields for current structure.
        """
        session_token = get_current_session_token()
        response = await profile_service.get_extended_stats(session_token)

        return {
            "data": response.data if response.is_success else None,
            "success": response.is_success,
            "available_fields": response.available_fields,
            "schema_description": response.schema_description,
        }

    @mcp.tool()
    async def get_achievements() -> dict:
        """
        Get all achievements for the current user.

        Returns list of achievements with unlocked status and progress.
        """
        session_token = get_current_session_token()
        achievements, response = await profile_service.get_achievements(session_token)

        unlocked = [a for a in achievements if a.unlocked]
        locked = [a for a in achievements if not a.unlocked]

        return {
            "summary": {
                "total": len(achievements),
                "unlocked": len(unlocked),
                "locked": len(locked),
                "completion_rate": f"{len(unlocked) / len(achievements) * 100:.1f}%" if achievements else "0%",
            },
            "unlocked_achievements": [
                {"name": a.name, "description": a.description, "unlocked_at": a.unlocked_at}
                for a in unlocked[:20]  # Limit for context
            ],
            "locked_achievements": [
                {"name": a.name, "description": a.description, "progress": a.progress}
                for a in locked[:10]  # Show some locked ones
            ],
        }

    @mcp.tool()
    async def get_comprehensive_profile() -> dict:
        """
        Get a comprehensive profile summary combining multiple data sources.

        Aggregates profile, stats, achievements, and more into a single response.
        Useful for getting a complete overview of the user's account.
        """
        session_token = get_current_session_token()
        return await profile_service.get_comprehensive_profile(session_token)

    @mcp.tool()
    async def get_user_maps() -> dict:
        """
        Get maps created by the current user.

        Returns list of custom maps with their details.
        """
        session_token = get_current_session_token()
        response = await profile_service.get_user_maps(session_token)

        return {
            "success": response.is_success,
            "data": response.summarize() if response.is_success else None,
            "available_fields": response.available_fields,
        }

    @mcp.tool()
    async def get_public_profile(user_id: str) -> dict:
        """
        Get another user's public profile.

        Args:
            user_id: The user's ID to look up

        Returns:
            Public profile information for the specified user
        """
        session_token = get_current_session_token()
        profile, response = await profile_service.get_public_profile(user_id, session_token)

        return {
            "profile": profile.to_dict(),
            "available_fields": response.available_fields,
        }
