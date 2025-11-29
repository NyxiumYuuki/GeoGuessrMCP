"""
GeoGuessr MCP Server Package.

A Model Context Protocol server for analyzing GeoGuessr game statistics
with automatic API monitoring and dynamic schema adaptation.
"""

__version__ = "0.2.0"
__author__ = "Yûki VACHOT"

from .main import main, mcp

__all__ = ["mcp", "main", "__version__", "__author__"]
