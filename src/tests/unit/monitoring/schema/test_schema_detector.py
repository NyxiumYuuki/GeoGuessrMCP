"""
Unit tests for the SchemaDetector class.

This module provides a suite of unit tests to validate the functionality of
the SchemaDetector class from the monitoring.schema package. The tests ensure
the correct detection and classification of data types, handling of nested
objects, computation of schema hashes, and parsing of specific data formats
such as datetime strings, URLs, and UUIDs.
"""

from geoguessr_mcp.monitoring.schema.SchemaDetector import SchemaDetector
from geoguessr_mcp.monitoring.schema.EndpointSchema import SchemaField


class TestSchemaDetector:
    """Tests for SchemaDetector class."""

    def test_detect_type_string(self):
        """Test string type detection."""
        detector = SchemaDetector()
        assert detector.detect_type("hello") == "string"

    def test_detect_type_integer(self):
        """Test integer type detection."""
        detector = SchemaDetector()
        assert detector.detect_type(42) == "integer"

    def test_detect_type_float(self):
        """Test float type detection."""
        detector = SchemaDetector()
        assert detector.detect_type(3.14) == "number"

    def test_detect_type_boolean(self):
        """Test boolean type detection."""
        detector = SchemaDetector()
        assert detector.detect_type(True) == "boolean"
        assert detector.detect_type(False) == "boolean"

    def test_detect_type_null(self):
        """Test null type detection."""
        detector = SchemaDetector()
        assert detector.detect_type(None) == "null"

    def test_detect_type_array(self):
        """Test array type detection."""
        detector = SchemaDetector()
        assert detector.detect_type([1, 2, 3]) == "array"

    def test_detect_type_object(self):
        """Test object type detection."""
        detector = SchemaDetector()
        assert detector.detect_type({"key": "value"}) == "object"

    def test_detect_type_datetime(self):
        """Test datetime string detection."""
        detector = SchemaDetector()
        assert detector.detect_type("2024-01-15T12:00:00Z") == "datetime"
        assert detector.detect_type("2024-01-15T12:00:00+00:00") == "datetime"

    def test_detect_type_uuid(self):
        """Test UUID string detection."""
        detector = SchemaDetector()
        assert detector.detect_type("550e8400-e29b-41d4-a716-446655440000") == "uuid"

    def test_detect_type_url(self):
        """Test URL string detection."""
        detector = SchemaDetector()
        assert detector.detect_type("https://example.com/path") == "url"
        assert detector.detect_type("http://test.com") == "url"

    def test_analyze_response_simple(self):
        """Test analyzing a simple response."""
        detector = SchemaDetector()
        data = {
            "id": "123",
            "name": "Test",
            "count": 42,
            "active": True,
        }

        fields = detector.analyze_response(data)

        assert len(fields) == 4
        assert fields["id"].field_type == "string"
        assert fields["name"].field_type == "string"
        assert fields["count"].field_type == "integer"
        assert fields["active"].field_type == "boolean"

    def test_analyze_response_nested(self):
        """Test analyzing a nested response."""
        detector = SchemaDetector()
        data = {
            "user": {
                "id": "123",
                "profile": {
                    "name": "Test",
                }
            }
        }

        fields = detector.analyze_response(data)

        assert "user" in fields
        assert fields["user"].field_type == "object"
        assert fields["user"].nested_schema is not None

    def test_compute_schema_hash(self):
        """Test schema hash computation."""
        detector = SchemaDetector()

        fields1 = {
            "id": SchemaField(name="id", field_type="string"),
            "name": SchemaField(name="name", field_type="string"),
        }

        fields2 = {
            "id": SchemaField(name="id", field_type="string"),
            "name": SchemaField(name="name", field_type="string"),
        }

        fields3 = {
            "id": SchemaField(name="id", field_type="integer"),  # Different type
            "name": SchemaField(name="name", field_type="string"),
        }

        hash1 = detector.compute_schema_hash(fields1)
        hash2 = detector.compute_schema_hash(fields2)
        hash3 = detector.compute_schema_hash(fields3)

        assert hash1 == hash2  # Same schema
        assert hash1 != hash3  # Different schema
