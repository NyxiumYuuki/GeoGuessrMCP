"""
A wrapper for handling API responses with dynamic schema integration.

This module provides a class, `DynamicResponse`, designed to work with API
responses by incorporating schema information from a dynamic schema registry.
It allows for easier interpretation and manipulation of the API response
data and its metadata.
"""

import logging
from typing import Any

from ..monitoring.schema.schema_registry import schema_registry

logger = logging.getLogger(__name__)


class DynamicResponse:
    """
    Wrapper for API responses with dynamic schema information.

    This class provides methods to access response data with awareness
    of the current schema, making it easier for the LLM to understand
    and process the data.
    """

    def __init__(
            self,
            data: Any,
            endpoint: str,
            status_code: int,
            response_time_ms: float,
    ):
        self.data = data
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self._schema = schema_registry.get_schema(endpoint)

    @property
    def is_success(self) -> bool:
        """Check if the request was successful."""
        return 200 <= self.status_code < 300

    @property
    def schema_description(self) -> str:
        """Get a human-readable description of the response schema."""
        return schema_registry.generate_dynamic_description(self.endpoint)

    @property
    def available_fields(self) -> list[str]:
        """Get list of available fields in this response."""
        if self._schema:
            return list(self._schema.fields.keys())
        if isinstance(self.data, dict):
            return list(self.data.keys())
        return []

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """
        Safely get a field from the response data.

        Supports nested field access using dot notation (e.g., "user.profile.name")
        """
        if not isinstance(self.data, dict):
            return default

        parts = field_name.split(".")
        current = self.data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def to_dict(self) -> dict:
        """Convert response to a dictionary with metadata."""
        return {
            "success": self.is_success,
            "status_code": self.status_code,
            "endpoint": self.endpoint,
            "response_time_ms": round(self.response_time_ms, 2),
            "data": self.data,
            "available_fields": self.available_fields,
        }

    def summarize(self, max_depth: int = 2) -> dict:
        """
        Create a summarized view of the response for LLM context.

        This reduces token usage while providing essential information.
        """

        def summarize_value(value: Any, depth: int) -> Any:
            if depth <= 0:
                if isinstance(value, (dict, list)):
                    return f"<{type(value).__name__} with {len(value)} items>"
                return value

            if isinstance(value, dict):
                return {k: summarize_value(v, depth - 1) for k, v in list(value.items())[:10]}
            if isinstance(value, list):
                if len(value) == 0:
                    return []
                return [
                    summarize_value(value[0], depth - 1),
                    f"... and {len(value) - 1} more items" if len(value) > 1 else None,
                ]
            if isinstance(value, str) and len(value) > 100:
                return value[:100] + "..."
            return value

        return {
            "endpoint": self.endpoint,
            "status": "success" if self.is_success else "error",
            "field_count": len(self.available_fields),
            "data_summary": summarize_value(self.data, max_depth),
        }
