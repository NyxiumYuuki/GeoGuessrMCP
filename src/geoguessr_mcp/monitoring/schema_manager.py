"""
Dynamic Schema Detection and Management.

This module automatically detects, tracks, and adapts to changes in API response formats.
It maintains a versioned history of schemas and provides tools for the LLM to understand
the current data structure.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class SchemaField:
    """Represents a single field in a schema."""
    name: str
    field_type: str
    nullable: bool = False
    nested_schema: Optional[dict] = None
    example_value: Any = None
    description: str = ""


@dataclass
class EndpointSchema:
    """Schema definition for an API endpoint."""
    endpoint: str
    method: str
    fields: dict[str, SchemaField] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_hash: str = ""
    response_code: int = 200
    is_available: bool = True
    error_message: Optional[str] = None
    sample_response: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "fields": {
                name: {
                    "name": f.name,
                    "field_type": f.field_type,
                    "nullable": f.nullable,
                    "nested_schema": f.nested_schema,
                    "example_value": self._serialize_example(f.example_value),
                    "description": f.description,
                }
                for name, f in self.fields.items()
            },
            "last_updated": self.last_updated.isoformat(),
            "schema_hash": self.schema_hash,
            "response_code": self.response_code,
            "is_available": self.is_available,
            "error_message": self.error_message,
            "sample_response": self.sample_response,
        }

    @staticmethod
    def _serialize_example(value: Any) -> Any:
        """Safely serialize example values."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, dict)):
            return str(value)[:100] + "..." if len(str(value)) > 100 else value
        return str(value)

    @classmethod
    def from_dict(cls, data: dict) -> "EndpointSchema":
        """Create from dictionary."""
        fields = {}
        for name, f_data in data.get("fields", {}).items():
            fields[name] = SchemaField(
                name=f_data["name"],
                field_type=f_data["field_type"],
                nullable=f_data.get("nullable", False),
                nested_schema=f_data.get("nested_schema"),
                example_value=f_data.get("example_value"),
                description=f_data.get("description", ""),
            )

        last_updated = data.get("last_updated")
        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated)
        else:
            last_updated = datetime.now(UTC)

        return cls(
            endpoint=data["endpoint"],
            method=data.get("method", "GET"),
            fields=fields,
            last_updated=last_updated,
            schema_hash=data.get("schema_hash", ""),
            response_code=data.get("response_code", 200),
            is_available=data.get("is_available", True),
            error_message=data.get("error_message"),
            sample_response=data.get("sample_response"),
        )


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
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
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

    def _analyze_object(
            self,
            obj: dict,
            fields: dict,
            prefix: str,
            remaining_depth: int
    ) -> None:
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
            {name: (f.field_type, f.nullable) for name, f in sorted(fields.items())},
            sort_keys=True
        )
        return hashlib.sha256(schema_repr.encode()).hexdigest()[:16]


class SchemaRegistry:
    """
    Manages schema storage, versioning, and change detection.

    Schemas are persisted to disk and loaded on startup, allowing the system
    to track changes over time and adapt automatically.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.SCHEMA_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.schemas: dict[str, EndpointSchema] = {}
        self.schema_history: dict[str, list[EndpointSchema]] = {}
        self.detector = SchemaDetector()
        self._load_cached_schemas()

    def _get_schema_file(self) -> Path:
        """Get the path to the schema cache file."""
        return self.cache_dir / "schemas.json"

    def _get_history_file(self) -> Path:
        """Get the path to the schema history file."""
        return self.cache_dir / "schema_history.json"

    def _load_cached_schemas(self) -> None:
        """Load schemas from disk cache."""
        schema_file = self._get_schema_file()
        if schema_file.exists():
            try:
                with open(schema_file) as f:
                    data = json.load(f)
                    for endpoint, schema_data in data.items():
                        self.schemas[endpoint] = EndpointSchema.from_dict(schema_data)
                logger.info(f"Loaded {len(self.schemas)} cached schemas")
            except Exception as e:
                logger.warning(f"Failed to load cached schemas: {e}")

        history_file = self._get_history_file()
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    for endpoint, history in data.items():
                        self.schema_history[endpoint] = [
                            EndpointSchema.from_dict(h) for h in history
                        ]
            except Exception as e:
                logger.warning(f"Failed to load schema history: {e}")

    def _save_schemas(self) -> None:
        """Save schemas to disk cache."""
        try:
            with open(self._get_schema_file(), "w") as f:
                json.dump(
                    {ep: schema.to_dict() for ep, schema in self.schemas.items()},
                    f,
                    indent=2
                )

            with open(self._get_history_file(), "w") as f:
                json.dump(
                    {
                        ep: [h.to_dict() for h in history[-10:]]  # Keep last 10 versions
                        for ep, history in self.schema_history.items()
                    },
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save schemas: {e}")

    def update_schema(
            self,
            endpoint: str,
            response_data: Any,
            response_code: int = 200,
            method: str = "GET"
    ) -> tuple[EndpointSchema, bool]:
        """
        Update schema for an endpoint based on response data.

        Args:
            endpoint: The API endpoint
            response_data: The JSON response data
            response_code: HTTP response code
            method: HTTP method

        Returns:
            Tuple of (updated schema, whether schema changed)
        """
        fields = self.detector.analyze_response(response_data)
        new_hash = self.detector.compute_schema_hash(fields)

        existing_schema = self.schemas.get(endpoint)
        schema_changed = existing_schema is None or existing_schema.schema_hash != new_hash

        new_schema = EndpointSchema(
            endpoint=endpoint,
            method=method,
            fields=fields,
            last_updated=datetime.now(UTC),
            schema_hash=new_hash,
            response_code=response_code,
            is_available=True,
            sample_response=self._truncate_sample(response_data),
        )

        if schema_changed:
            if endpoint not in self.schema_history:
                self.schema_history[endpoint] = []
            if existing_schema:
                self.schema_history[endpoint].append(existing_schema)
            logger.info(f"Schema changed for {endpoint}: {new_hash}")

        self.schemas[endpoint] = new_schema
        self._save_schemas()

        return new_schema, schema_changed

    def mark_unavailable(
            self,
            endpoint: str,
            error_message: str,
            response_code: int = 0
    ) -> None:
        """Mark an endpoint as unavailable."""
        if endpoint in self.schemas:
            self.schemas[endpoint].is_available = False
            self.schemas[endpoint].error_message = error_message
            self.schemas[endpoint].response_code = response_code
            self.schemas[endpoint].last_updated = datetime.now(UTC)
        else:
            self.schemas[endpoint] = EndpointSchema(
                endpoint=endpoint,
                method="GET",
                is_available=False,
                error_message=error_message,
                response_code=response_code,
            )
        self._save_schemas()

    def get_schema(self, endpoint: str) -> Optional[EndpointSchema]:
        """Get the current schema for an endpoint."""
        return self.schemas.get(endpoint)

    def get_all_schemas(self) -> dict[str, EndpointSchema]:
        """Get all registered schemas."""
        return self.schemas.copy()

    def get_available_endpoints(self) -> list[str]:
        """Get list of currently available endpoints."""
        return [ep for ep, schema in self.schemas.items() if schema.is_available]

    def get_schema_summary(self) -> dict:
        """Get a summary of all schemas for LLM context."""
        return {
            "total_endpoints": len(self.schemas),
            "available_endpoints": len(self.get_available_endpoints()),
            "endpoints": {
                endpoint: {
                    "available": schema.is_available,
                    "last_updated": schema.last_updated.isoformat(),
                    "field_count": len(schema.fields),
                    "fields": list(schema.fields.keys())[:20],  # Limit for context
                    "response_code": schema.response_code,
                }
                for endpoint, schema in self.schemas.items()
            }
        }

    def generate_dynamic_description(self, endpoint: str) -> str:
        """
        Generate a dynamic description of an endpoint's response format.
        This is used to provide context to the LLM about what data is available.
        """
        schema = self.get_schema(endpoint)
        if not schema:
            return f"No schema information available for {endpoint}"

        if not schema.is_available:
            return f"Endpoint {endpoint} is currently unavailable: {schema.error_message}"

        lines = [
            f"Endpoint: {endpoint}",
            f"Method: {schema.method}",
            f"Last Updated: {schema.last_updated.isoformat()}",
            f"Status: {'Available' if schema.is_available else 'Unavailable'}",
            "",
            "Response Fields:",
        ]

        for name, item in sorted(schema.fields.items()):
            nullable_str = " (nullable)" if item.nullable else ""
            lines.append(f"  - {name}: {item.field_type}{nullable_str}")
            if item.nested_schema:
                lines.append(f"    Nested fields: {list(item.nested_schema.keys())}")

        return "\n".join(lines)

    @staticmethod
    def _truncate_sample(data: Any, max_items: int = 3) -> Any:
        """Truncate sample response for storage."""
        if isinstance(data, dict):
            return {
                k: SchemaRegistry._truncate_sample(v, max_items)
                for k, v in list(data.items())[:20]
            }
        if isinstance(data, list):
            return [
                SchemaRegistry._truncate_sample(item, max_items)
                for item in data[:max_items]
            ]
        if isinstance(data, str) and len(data) > 200:
            return data[:200] + "..."
        return data


# Global registry instance
schema_registry = SchemaRegistry()
