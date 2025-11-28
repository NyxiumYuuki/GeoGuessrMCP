"""
Unit tests for the SchemaRegistry class.

This module contains test cases to verify the behavior of the
SchemaRegistry class, including the ability to update schemas,
store schema metadata, track schema availability, and retrieve
dynamic descriptions for endpoints.

Classes:
    TestSchemaRegistry: Contains test methods for testing schema
    registry functionality.
"""

from geoguessr_mcp.monitoring import SchemaRegistry


class TestSchemaRegistry:
    """Tests for SchemaRegistry class."""

    def test_update_schema_new(self, tmp_path):
        """Test adding a new schema."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        data = {"id": "123", "name": "Test"}
        schema, changed = registry.update_schema("/v3/test", data)

        assert changed is True
        assert schema.endpoint == "/v3/test"
        assert schema.is_available is True

    def test_update_schema_unchanged(self, tmp_path):
        """Test updating with same schema."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        data = {"id": "123", "name": "Test"}

        # First update
        schema1, changed1 = registry.update_schema("/v3/test", data)
        assert changed1 is True

        # Second update with same data
        schema2, changed2 = registry.update_schema("/v3/test", data)
        assert changed2 is False

    def test_update_schema_changed(self, tmp_path):
        """Test detecting schema changes."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        data1 = {"id": "123", "name": "Test"}
        data2 = {"id": "123", "name": "Test", "new_field": 42}  # Added field

        schema1, changed1 = registry.update_schema("/v3/test", data1)
        schema2, changed2 = registry.update_schema("/v3/test", data2)

        assert changed1 is True
        assert changed2 is True
        assert len(schema2.fields) > len(schema1.fields)

    def test_mark_unavailable(self, tmp_path):
        """Test marking endpoint as unavailable."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        registry.mark_unavailable("/v3/test", "Server error", 500)

        schema = registry.get_schema("/v3/test")
        assert schema is not None
        assert schema.is_available is False
        assert schema.error_message == "Server error"
        assert schema.response_code == 500

    def test_get_available_endpoints(self, tmp_path):
        """Test getting list of available endpoints."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        registry.update_schema("/v3/available", {"id": "1"})
        registry.mark_unavailable("/v3/unavailable", "Error")

        available = registry.get_available_endpoints()

        assert "/v3/available" in available
        assert "/v3/unavailable" not in available

    def test_generate_dynamic_description(self, tmp_path):
        """Test generating endpoint description."""
        registry = SchemaRegistry(cache_dir=str(tmp_path))

        registry.update_schema("/v3/test", {"id": "123", "name": "Test"})

        description = registry.generate_dynamic_description("/v3/test")

        assert "/v3/test" in description
        assert "id" in description
        assert "name" in description
