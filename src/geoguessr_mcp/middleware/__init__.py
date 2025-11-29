"""Middleware for GeoGuessr MCP Server."""

from .auth import AuthenticationMiddleware

__all__ = ["AuthenticationMiddleware"]
