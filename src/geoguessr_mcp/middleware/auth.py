"""
Authentication middleware for MCP server.

Provides Bearer token authentication for HTTP-based MCP transports.
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..config import settings

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API keys via Bearer token authentication.

    When MCP_AUTH_ENABLED is true, this middleware checks for a valid
    Authorization header with a Bearer token matching one of the configured API keys.
    """

    def __init__(self, app, valid_api_keys: Optional[set[str]] = None):
        super().__init__(app)
        self.valid_api_keys = valid_api_keys or settings.get_api_keys()
        self.enabled = settings.MCP_AUTH_ENABLED

        if self.enabled:
            if not self.valid_api_keys:
                logger.warning("Authentication is enabled but no API keys are configured!")
            else:
                logger.info(f"Authentication enabled with {len(self.valid_api_keys)} API key(s)")
        else:
            logger.info("Authentication is disabled")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and validate authentication if enabled."""

        # Skip authentication if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip authentication for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"Missing Authorization header from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Missing Authorization header. Use 'Authorization: Bearer YOUR_API_KEY'"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Parse Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization header format from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid Authorization header format. Use 'Authorization: Bearer YOUR_API_KEY'"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = parts[1]

        # Validate token against configured API keys
        if token not in self.valid_api_keys:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Invalid API key"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Authentication successful
        logger.debug(f"Authenticated request from {request.client.host}")

        # Proceed with the request
        response = await call_next(request)
        return response
