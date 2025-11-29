"""MCP Tools registration module."""

from mcp.server.fastmcp import FastMCP

from .analysis_tools import register_analysis_tools
from .auth_tools import register_auth_tools
from .game_tools import register_game_tools
from .monitoring_tools import register_monitoring_tools
from .profile_tools import register_profile_tools
from ..api.geoguessr_client import GeoGuessrClient
from ..auth.session import SessionManager
from ..config import settings
from ..services.analysis_service import AnalysisService
from ..services.game_service import GameService
from ..services.profile_service import ProfileService


def register_all_tools(mcp: FastMCP) -> dict:
    """
    Register all MCP tools with the server.

    Returns:
        Dictionary with initialized services for potential reuse
    """
    # Initialize core dependencies
    session_manager = SessionManager(default_cookie=settings.DEFAULT_NCFA_COOKIE)
    client = GeoGuessrClient(session_manager)

    # Initialize services
    profile_service = ProfileService(client)
    game_service = GameService(client)
    analysis_service = AnalysisService(client, game_service, profile_service)

    # Register all tool groups
    register_auth_tools(mcp, session_manager)
    register_profile_tools(mcp, profile_service)
    register_game_tools(mcp, game_service)
    register_analysis_tools(mcp, analysis_service)
    register_monitoring_tools(mcp)

    return {
        "session_manager": session_manager,
        "client": client,
        "profile_service": profile_service,
        "game_service": game_service,
        "analysis_service": analysis_service,
    }


__all__ = [
    "register_all_tools",
    "register_auth_tools",
    "register_profile_tools",
    "register_game_tools",
    "register_analysis_tools",
    "register_monitoring_tools",
]
