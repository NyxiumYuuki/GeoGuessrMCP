"""
GeoGuessr MCP Server - Main Entry Point.

This server provides tools for analyzing GeoGuessr game statistics,
with automatic API monitoring and dynamic schema adaptation.
"""

import logging
import sys

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .middleware import AuthenticationMiddleware
from .tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the server."""

    # Create the MCP server instance
    mcp = FastMCP(
        "GeoGuessr MCP",
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
    register_all_tools(mcp)

    # Get the ASGI application
    if settings.TRANSPORT == "streamable-http":
        mcp_app = mcp.streamable_http_app()
    elif settings.TRANSPORT == "sse":
        mcp_app = mcp.sse_app()
    else:
        logger.error("Unsupported transport: %s", settings.TRANSPORT)
        return

    # Always add CORS middleware for browser compatibility
    mcp_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup authentication middleware if enabled
    if settings.MCP_AUTH_ENABLED:
        logger.info("Setting up authentication middleware")
        mcp_app.add_middleware(AuthenticationMiddleware)

    logger.info(
        f"Starting GeoGuessr MCP Server on {settings.HOST}:{settings.PORT} "
        f"with {settings.TRANSPORT} transport"
    )

    if settings.MCP_AUTH_ENABLED:
        api_key_count = len(settings.get_api_keys())
        logger.info(f"MCP server authentication is ENABLED with {api_key_count} API key(s)")
    else:
        logger.warning("MCP server authentication is DISABLED - server is publicly accessible")

    if settings.DEFAULT_NCFA_COOKIE:
        logger.info("Default GeoGuessr authentication cookie configured from environment")
    else:
        logger.warning(
            "No default GeoGuessr authentication cookie set. "
            "Users will need to login or provide a cookie."
        )

    # Run the server with the modified app (with middleware)
    uvicorn.run(
        mcp_app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
