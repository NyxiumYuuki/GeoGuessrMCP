"""
GeoGuessr MCP Server - Main Entry Point.

This server provides tools for analyzing GeoGuessr game statistics,
with automatic API monitoring and dynamic schema adaptation.
"""

import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware

from .config import settings
from .middleware import AuthenticationMiddleware
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

# Setup authentication middleware if enabled
if settings.MCP_AUTH_ENABLED:
    logger.info("Setting up authentication middleware")

    # Create a function to add middleware to the app
    def add_middleware_to_app(app):
        """Add authentication middleware to a Starlette app."""
        if app is not None:
            try:
                app.add_middleware(AuthenticationMiddleware)
                logger.info("Authentication middleware successfully added")
                return True
            except Exception as e:
                logger.error(f"Failed to add middleware: {e}")
        return False

    # Try to add middleware immediately to any existing app
    middleware_added = False

    # Try different possible locations where FastMCP might store the app
    for attr_path in [
        "mcp._transport.app",
        "mcp.sse.app",
        "mcp.http_server.app",
        "mcp._http_server.app",
        "mcp._app",
        "mcp._asgi_app",
    ]:
        try:
            parts = attr_path.split(".")
            obj = mcp
            for part in parts[1:]:  # Skip 'mcp' itself
                obj = getattr(obj, part, None)
                if obj is None:
                    break

            if obj is not None and add_middleware_to_app(obj):
                middleware_added = True
                break
        except (AttributeError, TypeError):
            continue

    if not middleware_added:
        # If we couldn't add it immediately, wrap the run method
        logger.info("Deferring middleware addition until server starts")

        _original_run = mcp.run

        def run_with_middleware_wrapper(*args, **kwargs):
            """Wrapper to try adding middleware when run() is called."""
            # Try again when run is called
            for attr_path in [
                "mcp._transport.app",
                "mcp.sse.app",
                "mcp.http_server.app",
                "mcp._http_server.app",
                "mcp._app",
                "mcp._asgi_app",
            ]:
                try:
                    parts = attr_path.split(".")
                    obj = mcp
                    for part in parts[1:]:
                        obj = getattr(obj, part, None)
                        if obj is None:
                            break

                    if obj is not None and add_middleware_to_app(obj):
                        break
                except (AttributeError, TypeError):
                    continue

            return _original_run(*args, **kwargs)

        mcp.run = run_with_middleware_wrapper


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

    # Run the server
    mcp.run(transport=settings.TRANSPORT)


if __name__ == "__main__":
    main()
