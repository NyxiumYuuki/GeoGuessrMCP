"""
Module to register monitoring tools for analyzing API endpoints and schemas.

This module provides a set of monitoring tools that allow checking the status
and availability of API endpoints, exploring their response schemas, and
tracking changes to API structures. These tools are integrated with the FastMCP
framework and can be used to comprehensively monitor API performance and
evolution.
"""

from mcp.server.fastmcp import FastMCP

from ..monitoring import endpoint_monitor, schema_registry
from .auth_tools import get_current_session_token


def register_monitoring_tools(mcp: FastMCP):
    """Register monitoring-related tools."""

    @mcp.tool()
    async def check_api_status() -> dict:
        """
        Check the availability and status of all monitored API endpoints.

        Runs a full check of all known GeoGuessr API endpoints and reports
        their availability, response times, and any schema changes detected.

        Returns:
            Comprehensive API status report including
            - Number of available/unavailable endpoints
            - Response times
            - Recent schema changes
            - Error details for failed endpoints
        """
        # Update monitor with current auth
        session_token = get_current_session_token()
        if session_token:
            from ..auth.session import SessionManager

            session_manager = SessionManager()
            session = await session_manager.get_session(session_token)
            if session:
                endpoint_monitor.ncfa_cookie = session.ncfa_cookie

        await endpoint_monitor.run_full_check()
        return endpoint_monitor.get_monitoring_report()

    @mcp.tool()
    async def get_endpoint_schema(endpoint: str) -> dict:
        """
        Get the current schema information for a specific API endpoint.

        Provides detailed information about the response format of an endpoint,
        including all fields, their types, and example values. This is useful
        for understanding what data is available from each endpoint.

        Args:
            endpoint: The API endpoint path (e.g., "/v3/profiles")

        Returns:
            Schema information including
            - Field names and types
            - Whether the endpoint is currently available
            - When the schema was last updated
            - Sample response structure
        """
        schema = schema_registry.get_schema(endpoint)

        if not schema:
            return {
                "found": False,
                "message": f"No schema information available for {endpoint}",
                "available_endpoints": schema_registry.get_available_endpoints(),
            }

        return {
            "found": True,
            "endpoint": schema.endpoint,
            "method": schema.method,
            "is_available": schema.is_available,
            "last_updated": schema.last_updated.isoformat(),
            "response_code": schema.response_code,
            "field_count": len(schema.fields),
            "fields": {
                name: {
                    "type": field.field_type,
                    "nullable": field.nullable,
                    "has_nested": field.nested_schema is not None,
                }
                for name, field in list(schema.fields.items())[:30]  # Limit for context
            },
            "error_message": schema.error_message,
        }

    @mcp.tool()
    async def list_available_endpoints() -> dict:
        """
        List all known API endpoints and their current status.

        Returns a summary of all monitored endpoints including which ones
        are currently available and when they were last checked.

        Returns:
            List of endpoints with availability status
        """
        summary = schema_registry.get_schema_summary()

        return {
            "total_endpoints": summary["total_endpoints"],
            "available_count": summary["available_endpoints"],
            "endpoints": {
                ep: {
                    "available": info["available"],
                    "field_count": info["field_count"],
                    "last_updated": info["last_updated"],
                }
                for ep, info in summary["endpoints"].items()
            },
        }

    @mcp.tool()
    async def get_schema_changes() -> dict:
        """
        Get information about recent schema changes detected in the API.

        Shows endpoints where the response format has changed since the
        last check. This is useful for understanding API evolution.

        Returns:
            List of endpoints with schema changes and change details
        """
        changes = []

        for endpoint, history in schema_registry.schema_history.items():
            if len(history) > 0:
                current = schema_registry.get_schema(endpoint)
                previous = history[-1] if history else None

                if current and previous:
                    changes.append(
                        {
                            "endpoint": endpoint,
                            "current_hash": current.schema_hash,
                            "previous_hash": previous.schema_hash,
                            "current_fields": len(current.fields),
                            "previous_fields": len(previous.fields),
                            "changed_at": current.last_updated.isoformat(),
                        }
                    )

        return {
            "total_changes_tracked": len(changes),
            "changes": changes,
        }

    @mcp.tool()
    async def explore_endpoint(path: str, use_game_server: bool = False) -> dict:
        """
        Explore an unknown or new API endpoint.

        Makes a request to the specified endpoint and analyzes the response
        to discover its schema. Useful for discovering new endpoints or
        testing endpoint availability.

        Args:
            path: The API endpoint path to explore (e.g., "/v3/new-endpoint")
            use_game_server: Whether to use the game server URL instead of main API

        Returns:
            Response analysis including discovered schema and sample data
        """
        session_token = get_current_session_token()

        from ..api.dynamic_response import GeoGuessrClient
        from ..auth.session import SessionManager

        session_manager = SessionManager()
        client = GeoGuessrClient(session_manager)

        try:
            response = await client.get_raw(
                path,
                session_token,
                use_game_server=use_game_server,
            )

            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "response_time_ms": round(response.response_time_ms, 2),
                "discovered_fields": response.available_fields,
                "schema_description": response.schema_description,
                "data_preview": response.summarize(max_depth=2),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path,
            }
