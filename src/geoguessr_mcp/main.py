"""
GeoGuessr MCP Server - Main Entry Point.

This server provides tools for analyzing GeoGuessr game statistics,
with automatic API monitoring and dynamic schema adaptation.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import settings
from .monitoring import endpoint_monitor
from .tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# Create the MCP server instance
mcp = FastMCP(
    "GeoGuessr Analyzer",
    instructions="""
    MCP server for analyzing GeoGuessr game statistics and optimizing gameplay strategy.
    
    This server provides:
    - Profile and statistics retrieval
    - Game history and analysis
    - Performance tracking and recommendations
    - API monitoring with automatic schema adaptation
    
    The server automatically tracks API endpoint changes and adapts to response format
    modifications. Use the monitoring tools to check API status and discover available data.
    
    Authentication:
    - Use 'login(email, password)' to authenticate with your GeoGuessr account
    - Or use 'set_ncfa_cookie(cookie)' with a cookie from your browser
    - Or set GEOGUESSR_NCFA_COOKIE environment variable for automatic auth
    
    Key tools:
    - get_performance_summary() - Comprehensive overview of your account
    - analyze_recent_games(count) - Analyze your recent gameplay
    - get_strategy_recommendations() - Get personalized improvement tips
    - check_api_status() - Monitor API endpoint availability
    - explore_endpoint(path) - Discover new API endpoints
    """,
    host=settings.HOST,
    port=settings.PORT,
)

# Register all tools
services = register_all_tools(mcp)


async def start_background_tasks():
    """Start background monitoring tasks."""
    if settings.MONITORING_ENABLED:
        logger.info("Starting API monitoring background task...")
        await endpoint_monitor.start_periodic_monitoring()


async def stop_background_tasks():
    """Stop background monitoring tasks."""
    if endpoint_monitor._running:
        await endpoint_monitor.stop_monitoring()


def main():
    """Main entry point for the server."""
    logger.info(
        f"Starting GeoGuessr MCP Server on {settings.HOST}:{settings.PORT} "
        f"with {settings.TRANSPORT} transport"
    )

    if settings.DEFAULT_NCFA_COOKIE:
        logger.info("Default authentication cookie configured from environment")
    else:
        logger.warning(
            "No default authentication cookie set. " "Users will need to login or provide a cookie."
        )

    # Run the server
    mcp.run(transport=settings.TRANSPORT)


if __name__ == "__main__":
    main()
