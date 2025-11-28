"""MCP tools for profile operations."""

from mcp.server.fastmcp import FastMCP

from ..services.profile_service import ProfileService


def register_profile_tools(mcp: FastMCP, profile_service: ProfileService):
    """Register profile-related tools."""

    @mcp.tool()
    async def get_my_profile(session_token: str = "") -> dict:
        """Get the current user's profile information."""
        profile = await profile_service.get_profile(session_token if session_token else None)
        return {
            "id": profile.id,
            "nick": profile.nick,
            "email": profile.email,
            "country": profile.country,
            "level": profile.level,
        }

    @mcp.tool()
    async def get_my_stats(session_token: str = "") -> dict:
        """Get the current user's statistics."""
        return await profile_service.get_stats(session_token if session_token else None)
