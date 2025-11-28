"""Main entry point for the Geoguessr MCP Server."""

from mcp.server.fastmcp import FastMCP

from .config import settings
from .tools import register_all_tools

mcp = FastMCP(
    "Geoguessr Analyzer",
    instructions="MCP server for analyzing Geoguessr game statistics",
    host=settings.HOST,
    port=settings.PORT,
)

# Register all tools
register_all_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport=settings.TRANSPORT)
