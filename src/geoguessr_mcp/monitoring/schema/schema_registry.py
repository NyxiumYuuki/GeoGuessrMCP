"""
Handles schema versioning, storage, and updates for API endpoints.

The module provides functionality to detect and manage changes in API response
schemas, maintain history of schema versions, and persist schema data to disk.
It supports use cases such as tracking endpoint availability, generating schema
summaries, and providing dynamic endpoint descriptions.

Classes:
    SchemaRegistry
"""

import json
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .endpoint_schema import EndpointSchema
from .schema_detector import SchemaDetector
from ...config import settings

logger = logging.getLogger(__name__)


class SchemaRegistry:
    """
    Manages schema storage, versioning, and change detection.

    Schemas are persisted to disk and loaded on startup, allowing the system
    to track changes over time and adapt automatically.
    """

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or settings.SCHEMA_CACHE_DIR)

        # Try to create the cache directory, fall back to temp if permission denied
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(
                f"Cannot create schema cache directory at {self.cache_dir}: {e}. "
                f"Using temporary directory instead."
            )
            # Use a temporary directory that will be cleaned up
            temp_dir = tempfile.mkdtemp(prefix="geoguessr_schema_")
            self.cache_dir = Path(temp_dir)
            logger.info(f"Using temporary schema cache directory: {self.cache_dir}")

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
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to load cached schemas due to corrupted JSON: {e}. "
                    f"Removing corrupted cache file."
                )
                try:
                    schema_file.unlink()
                    logger.info(f"Removed corrupted schema cache file: {schema_file}")
                except Exception as rm_error:
                    logger.error(f"Failed to remove corrupted cache file: {rm_error}")
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
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to load schema history due to corrupted JSON: {e}. "
                    f"Removing corrupted history file."
                )
                try:
                    history_file.unlink()
                    logger.info(f"Removed corrupted schema history file: {history_file}")
                except Exception as rm_error:
                    logger.error(f"Failed to remove corrupted history file: {rm_error}")
            except Exception as e:
                logger.warning(f"Failed to load schema history: {e}")

    def _save_schemas(self) -> None:
        """Save schemas to disk cache."""
        try:
            with open(self._get_schema_file(), "w") as f:
                json.dump(
                    {ep: schema.to_dict() for ep, schema in self.schemas.items()}, f, indent=2
                )

            with open(self._get_history_file(), "w") as f:
                json.dump(
                    {
                        ep: [h.to_dict() for h in history[-10:]]  # Keep last 10 versions
                        for ep, history in self.schema_history.items()
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save schemas: {e}")

    def update_schema(
        self, endpoint: str, response_data: Any, response_code: int = 200, method: str = "GET"
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

    def mark_unavailable(self, endpoint: str, error_message: str, response_code: int = 0) -> None:
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

    def get_schema(self, endpoint: str) -> EndpointSchema | None:
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
            },
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
                k: SchemaRegistry._truncate_sample(v, max_items) for k, v in list(data.items())[:20]
            }
        if isinstance(data, list):
            return [SchemaRegistry._truncate_sample(item, max_items) for item in data[:max_items]]
        if isinstance(data, str) and len(data) > 200:
            return data[:200] + "..."
        return data


# Global registry instance
schema_registry = SchemaRegistry()
