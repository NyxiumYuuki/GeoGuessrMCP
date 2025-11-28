"""
Module for testing the EndpointSchema class and its functionality.

This module contains unit tests for the EndpointSchema class, focusing on
the serialization and deserialization functionality. The tests validate
the `to_dict` and `from_dict` methods, ensuring correct conversion between
dictionary representation and the EndpointSchema object.
"""

from geoguessr_mcp.monitoring import EndpointSchema, SchemaField


class TestEndpointSchema:
    """Tests for EndpointSchema class."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        schema = EndpointSchema(
            endpoint="/v3/profiles",
            method="GET",
            fields={
                "id": SchemaField(name="id", field_type="string"),
            },
            response_code=200,
            is_available=True,
        )

        result = schema.to_dict()

        assert result["endpoint"] == "/v3/profiles"
        assert result["method"] == "GET"
        assert result["is_available"] is True
        assert "id" in result["fields"]

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "endpoint": "/v3/profiles",
            "method": "GET",
            "fields": {
                "id": {
                    "name": "id",
                    "field_type": "string",
                    "nullable": False,
                }
            },
            "last_updated": "2024-01-15T12:00:00+00:00",
            "schema_hash": "abc123",
            "response_code": 200,
            "is_available": True,
        }

        schema = EndpointSchema.from_dict(data)

        assert schema.endpoint == "/v3/profiles"
        assert schema.method == "GET"
        assert "id" in schema.fields
        assert schema.fields["id"].field_type == "string"
