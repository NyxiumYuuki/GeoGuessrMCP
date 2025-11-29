"""
Schema definitions and utility methods for managing API endpoints.

This module provides the `EndpointSchema` class, which offers the ability
to define the schema of an API endpoint, serialize and deserialize data, and
manage metadata such as response codes and availability. The class also
includes helper utilities for handling data transformations and validating
schema information.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from .schema_field import SchemaField

logger = logging.getLogger(__name__)


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
