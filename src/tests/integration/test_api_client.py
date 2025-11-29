"""
Integration tests for the GeoGuessr API client.

These tests verify the API client functionality with mocked HTTP responses,
simulating real API interactions without making actual network calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from geoguessr_mcp.api import DynamicResponse, GeoGuessrClient, EndpointInfo, Endpoints
from geoguessr_mcp.config import settings


class TestDynamicResponse:
    """Tests for DynamicResponse wrapper class."""

    def test_is_success_200(self):
        """Test success detection for 200 status code."""
        response = DynamicResponse(
            data={"id": "123"},
            endpoint="/v3/profiles",
            status_code=200,
            response_time_ms=150.0,
        )
        assert response.is_success is True

    def test_is_success_201(self):
        """Test success detection for 201 status code."""
        response = DynamicResponse(
            data={"created": True},
            endpoint="/v3/games",
            status_code=201,
            response_time_ms=200.0,
        )
        assert response.is_success is True

    def test_is_success_failure(self):
        """Test success detection for error status codes."""
        response = DynamicResponse(
            data={"error": "Not found"},
            endpoint="/v3/profiles",
            status_code=404,
            response_time_ms=100.0,
        )
        assert response.is_success is False

    def test_available_fields_dict(self):
        """Test available_fields with dict data."""
        response = DynamicResponse(
            data={"id": "123", "name": "Test", "score": 5000},
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        assert response.available_fields == ["id", "name", "score"]

    def test_available_fields_non_dict(self):
        """Test available_fields with non-dict data."""
        response = DynamicResponse(
            data=["item1", "item2"],
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        assert response.available_fields == []

    def test_get_field_simple(self):
        """Test getting a simple field."""
        response = DynamicResponse(
            data={"id": "123", "name": "Test"},
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        assert response.get_field("id") == "123"
        assert response.get_field("name") == "Test"

    def test_get_field_nested(self):
        """Test getting a nested field with dot notation."""
        response = DynamicResponse(
            data={
                "user": {
                    "profile": {
                        "name": "TestUser",
                        "level": 50,
                    }
                }
            },
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        assert response.get_field("user.profile.name") == "TestUser"
        assert response.get_field("user.profile.level") == 50

    def test_get_field_missing_with_default(self):
        """Test getting missing field returns default."""
        response = DynamicResponse(
            data={"id": "123"},
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        assert response.get_field("missing", default="default_value") == "default_value"
        assert response.get_field("nested.missing", default=None) is None

    def test_to_dict(self):
        """Test converting response to dict."""
        response = DynamicResponse(
            data={"id": "123"},
            endpoint="/v3/profiles",
            status_code=200,
            response_time_ms=150.5,
        )
        result = response.to_dict()

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["endpoint"] == "/v3/profiles"
        assert result["response_time_ms"] == 150.5
        assert result["data"] == {"id": "123"}
        assert "available_fields" in result

    def test_summarize(self):
        """Test response summarization."""
        response = DynamicResponse(
            data={
                "items": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"},
                    {"id": 3, "name": "Item 3"},
                    {"id": 4, "name": "Item 4"},
                ],
                "total": 4,
            },
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        summary = response.summarize(max_depth=1)

        assert summary["endpoint"] == "/mock/endpoint"
        assert summary["status"] == "success"
        assert "data_summary" in summary

    def test_summarize_long_string(self):
        """Test that long strings are truncated in summaries."""
        long_text = "x" * 200
        response = DynamicResponse(
            data={"description": long_text},
            endpoint="/mock/endpoint",
            status_code=200,
            response_time_ms=100.0,
        )
        summary = response.summarize(max_depth=2)

        # The long string should be truncated
        assert len(summary["data_summary"]["description"]) <= 103  # 100 + "..."


class TestGeoGuessrClient:
    """Tests for GeoGuessrClient."""

    @pytest.mark.asyncio
    async def test_get_authenticated_client(self, client, mock_session_manager):
        """Test getting authenticated HTTP client."""
        http_client = await client._get_authenticated_client()

        assert http_client is not None
        mock_session_manager.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_authenticated_client_no_session(self, mock_session_manager):
        """Test error when no session is available."""
        mock_session_manager.get_session = AsyncMock(return_value=None)
        client = GeoGuessrClient(mock_session_manager)

        with pytest.raises(ValueError, match="No valid session available"):
            await client._get_authenticated_client()

    def test_get_base_url_main_api(self, client):
        """Test base URL selection for main API."""
        endpoint = EndpointInfo(path="/v3/profiles", use_game_server=False)
        url = client._get_base_url(endpoint)
        assert url == settings.GEOGUESSR_API_URL

    def test_get_base_url_game_server(self, client):
        """Test base URL selection for game server."""
        endpoint = EndpointInfo(path="/tournaments", use_game_server=True)
        url = client._get_base_url(endpoint)
        assert url == settings.GAME_SERVER_URL

    @pytest.mark.asyncio
    async def test_get_request_success(self, client):
        """Test successful GET request."""
        with patch.object(client, "_get_authenticated_client") as mock_auth:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123", "nick": "TestUser"}
            mock_http_client.get = AsyncMock(return_value=mock_response)

            mock_auth.return_value = mock_http_client

            response = await client.get(Endpoints.PROFILES.GET_PROFILE)

            assert response.is_success
            assert response.data["id"] == "123"

    @pytest.mark.asyncio
    async def test_get_request_failure(self, client):
        """Test failed GET request."""
        with patch.object(client, "_get_authenticated_client") as mock_auth:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_http_client.get = AsyncMock(return_value=mock_response)

            mock_auth.return_value = mock_http_client

            response = await client.get(Endpoints.PROFILES.GET_PROFILE)

            assert not response.is_success
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_request(self, client):
        """Test POST request."""
        with patch.object(client, "_get_authenticated_client") as mock_auth:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_http_client.post = AsyncMock(return_value=mock_response)

            mock_auth.return_value = mock_http_client

            endpoint = EndpointInfo(path="/mock/endpoint", method="POST")
            response = await client.post(endpoint, json_data={"data": "test"})

            assert response.is_success

    @pytest.mark.asyncio
    async def test_get_raw_request(self, client):
        """Test raw GET request to arbitrary path."""
        with patch.object(client, "_get_authenticated_client") as mock_auth:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"discovered": True}
            mock_http_client.get = AsyncMock(return_value=mock_response)

            mock_auth.return_value = mock_http_client

            response = await client.get_raw("/v3/unknown-endpoint")

            assert response.is_success
            assert response.endpoint == "/v3/unknown-endpoint"

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test handling of timeout exceptions."""
        with patch.object(client, "_get_authenticated_client") as mock_auth:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__.return_value = mock_http_client
            mock_http_client.__aexit__.return_value = None
            mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            mock_auth.return_value = mock_http_client

            with pytest.raises(httpx.TimeoutException):
                await client.get(Endpoints.PROFILES.GET_PROFILE)


@pytest.mark.integration
@pytest.mark.real_env
class TestGeoGuessrClientIntegration:
    """
    Integration tests that would make real API calls.

    These tests are marked with @pytest.mark.integration and should only
    be run when explicitly requested (pytest -m integration) with a valid
    authentication cookie.
    """

    @pytest.mark.asyncio
    async def test_real_profile_endpoint(self, real_client):
        """Test real API call to profile endpoint."""
        # This test requires GEOGUESSR_NCFA_COOKIE to be set
        import os
        if not os.environ.get("GEOGUESSR_NCFA_COOKIE"):
            pytest.skip("GEOGUESSR_NCFA_COOKIE not set")

        response = await real_client.get(Endpoints.PROFILES.GET_PROFILE)

        assert response.is_success
        assert "user" in response.available_fields or "email" in response.available_fields

    @pytest.mark.asyncio
    async def test_real_stats_endpoint(self, real_client):
        """Test real API call to stats' endpoint."""
        # This test requires GEOGUESSR_NCFA_COOKIE to be set
        import os
        if not os.environ.get("GEOGUESSR_NCFA_COOKIE"):
            pytest.skip("GEOGUESSR_NCFA_COOKIE not set")

        response = await real_client.get(Endpoints.PROFILES.GET_STATS)

        assert response.is_success
        # Stats' endpoint should have some numeric data
        assert len(response.available_fields) > 0
