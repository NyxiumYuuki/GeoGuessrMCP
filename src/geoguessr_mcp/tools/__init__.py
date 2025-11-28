"""Register all MCP tools."""

from mcp.server.fastmcp import FastMCP

from ..api.client import GeoguessrClient
from ..auth.session import SessionManager
from ..services.analysis_service import AnalysisService
from ..services.game_service import GameService
from ..services.profile_service import ProfileService
from .analysis_tools import register_analysis_tools
from .auth_tools import register_auth_tools
from .game_tools import register_game_tools
from .profile_tools import register_profile_tools


def register_all_tools(mcp: FastMCP):
    """Register all tools with the MCP server."""
    # Initialize dependencies
    session_manager = SessionManager()
    client = GeoguessrClient(session_manager)

    # Initialize services
    profile_service = ProfileService(client)
    game_service = GameService(client)
    analysis_service = AnalysisService()

    # Register tools
    register_auth_tools(mcp, session_manager)
    register_profile_tools(mcp, profile_service)
    register_game_tools(mcp, game_service)
    register_analysis_tools(mcp, analysis_service, game_service)
