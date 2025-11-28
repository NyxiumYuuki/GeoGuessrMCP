"""
Represents a single field in a schema.

This module defines a dataclass that encapsulates the attributes of
a schema field, including its name, type, and other relevant metadata.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SchemaField:
    """Represents a single field in a schema."""
    name: str
    field_type: str
    nullable: bool = False
    nested_schema: Optional[dict] = None
    example_value: Any = None
    description: str = ""
