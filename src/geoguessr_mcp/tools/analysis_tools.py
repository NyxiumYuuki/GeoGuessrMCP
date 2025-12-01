"""
This module provides tools for analyzing and improving game performance
by registering multiple analysis-related functions to a given `FastMCP`
instance. These tools include functionalities for analyzing recent games,
retrieving performance summaries, and generating strategy recommendations.

The functions leverage an external analysis service to compute detailed
statistics and insights based on gameplay data and user profiles. Each tool
offers asynchronous execution for efficient performance.
"""

from mcp.server.fastmcp import FastMCP

from ..services.analysis_service import AnalysisService
from .auth_tools import get_current_session_token


def register_analysis_tools(mcp: FastMCP, analysis_service: AnalysisService):
    """Register analysis-related tools."""

    @mcp.tool()
    async def analyze_recent_games(count: int = 10) -> dict:
        """
        Analyze recent games and provide statistics summary.

        Fetches recent games and calculates aggregate statistics including
        average scores, perfect round rates, and performance trends.

        Args:
            count: Number of recent games to analyze (default: 10)

        Returns:
            Comprehensive analysis with statistics and individual game data
        """
        session_token = get_current_session_token()
        return await analysis_service.analyze_recent_games(count, session_token)

    @mcp.tool()
    async def get_performance_summary() -> dict:
        """
        Get a comprehensive performance summary.

        Combines profile stats, achievements, season information, and
        recent game analysis into a single overview. Useful for understanding
        overall account status and progress.

        Returns:
            Aggregated performance data from multiple API endpoints
        """
        session_token = get_current_session_token()
        return await analysis_service.get_performance_summary(session_token)

    @mcp.tool()
    async def get_strategy_recommendations() -> dict:
        """
        Get personalized strategy recommendations.

        Analyzes gameplay patterns and provides actionable recommendations
        for improving performance. Considers factors like:
        - Perfect round rate
        - Time management
        - Score trends
        - Weak areas

        Returns:
            Analysis summary and prioritized recommendations
        """
        session_token = get_current_session_token()
        return await analysis_service.get_strategy_recommendations(session_token)
