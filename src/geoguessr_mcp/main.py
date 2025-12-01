"""
GeoGuessr MCP Server - Main Entry Point.

This server provides tools for analyzing GeoGuessr game statistics,
with automatic API monitoring and dynamic schema adaptation.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

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


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request details for debugging."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        logger.debug(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")

        response = await call_next(request)

        if response.status_code >= 400:
            logger.warning(
                f"Error response: {request.method} {request.url.path} -> {response.status_code}"
            )

        return response


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

    # Wrap the streamable_http_app method to inject middleware
    _original_streamable_http_app = mcp.streamable_http_app

    def _streamable_http_app_with_middleware():
        """Wrap app creation to inject middleware."""
        app = _original_streamable_http_app()

        # Add request logging middleware for debugging (first in chain)
        if settings.LOG_LEVEL == "DEBUG":
            app.add_middleware(RequestLoggingMiddleware)

        # Always add CORS middleware for browser compatibility
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
        )

        # Add authentication middleware if enabled
        if settings.MCP_AUTH_ENABLED:
            app.add_middleware(AuthenticationMiddleware)

        return app

    # Replace the method with our wrapper
    mcp.streamable_http_app = _streamable_http_app_with_middleware

    # Also wrap sse_app for SSE transport
    if hasattr(mcp, "sse_app"):
        _original_sse_app = mcp.sse_app

        def _sse_app_with_middleware():
            """Wrap SSE app creation to inject middleware."""
            app = _original_sse_app()

            if settings.LOG_LEVEL == "DEBUG":
                app.add_middleware(RequestLoggingMiddleware)

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
                expose_headers=["mcp-session-id", "mcp-protocol-version"],
            )

            if settings.MCP_AUTH_ENABLED:
                app.add_middleware(AuthenticationMiddleware)

            return app

        mcp.sse_app = _sse_app_with_middleware

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

    # Run the server - middleware will be applied via our wrapper
    mcp.run(transport=settings.TRANSPORT)


if __name__ == "__main__":
    main()
