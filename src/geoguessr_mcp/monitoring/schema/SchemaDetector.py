"""
This module provides a dynamic JSON schema detection and analysis utility.

It includes functionality to infer types of various data values, analyze JSON
response structures, compute schema hashes, and identify nested schemas.
The module is particularly useful for understanding and working with
dynamic JSON datasets and detecting changes in schema over time.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from .SchemaField import SchemaField

logger = logging.getLogger(__name__)


class SchemaDetector:
    """Detects and analyzes JSON response schemas dynamically."""

    @staticmethod
    def detect_type(value: Any) -> str:
        """Detect the type of value."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            # Try to detect special string types
            if SchemaDetector._is_iso_datetime(value):
                return "datetime"
            if SchemaDetector._is_uuid(value):
                return "uuid"
            if SchemaDetector._is_url(value):
                return "url"
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "unknown"

    @staticmethod
    def _is_iso_datetime(value: str) -> bool:
        """Check if string is ISO datetime format."""
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _is_uuid(value: str) -> bool:
        """Check if string is UUID format."""
        import re

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(uuid_pattern, value.lower()))

    @staticmethod
    def _is_url(value: str) -> bool:
        """Check if string is URL format."""
        return value.startswith(("http://", "https://"))

    def analyze_response(self, data: Any, max_depth: int = 5) -> dict[str, SchemaField]:
        """
        Analyze a JSON response and extract its schema.

        Args:
            data: The JSON response data
            max_depth: Maximum depth for nested object analysis

        Returns:
            Dictionary mapping field names to SchemaField objects
        """
        if not isinstance(data, dict):
            return {}

        fields = {}
        self._analyze_object(data, fields, "", max_depth)
        return fields

    def _analyze_object(self, obj: dict, fields: dict, prefix: str, remaining_depth: int) -> None:
        """Recursively analyze an object and extract field information."""
        if remaining_depth <= 0:
            return

        for key, value in obj.items():
            field_name = f"{prefix}.{key}" if prefix else key
            field_type = self.detect_type(value)

            nested_schema = None
            if field_type == "object" and isinstance(value, dict):
                nested_schema = {}
                self._analyze_object(value, nested_schema, "", remaining_depth - 1)
            elif field_type == "array" and value and isinstance(value[0], dict):
                nested_schema = {}
                self._analyze_object(value[0], nested_schema, "", remaining_depth - 1)

            fields[field_name] = SchemaField(
                name=field_name,
                field_type=field_type,
                nullable=value is None,
                nested_schema=nested_schema if nested_schema else None,
                example_value=value,
            )

    @staticmethod
    def compute_schema_hash(fields: dict[str, SchemaField]) -> str:
        """Compute a hash of the schema for change detection."""
        schema_repr = json.dumps(
            {name: (f.field_type, f.nullable) for name, f in sorted(fields.items())}, sort_keys=True
        )
        return hashlib.sha256(schema_repr.encode()).hexdigest()[:16]
