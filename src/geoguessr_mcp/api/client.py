"""
Dynamic HTTP client for GeoGuessr API communication.

This client automatically handles authentication, endpoint routing,
and integrates with the schema registry for dynamic response handling.
"""

import logging
from typing import Any, Optional

import httpx

from ..auth.session import SessionManager
from ..config import settings
from ..monitoring.schema_manager import schema_registry
from .endpoints import EndpointInfo

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
                return {
                    k: summarize_value(v, depth - 1)
                    for k, v in list(value.items())[:10]
                }
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


class GeoGuessrClient:
    """
    Dynamic HTTP client for GeoGuessr API.

    Features:
    - Automatic authentication handling
    - Dynamic response schema tracking
    - Retry logic with exponential backoff
    - Integrated monitoring and logging
    """

    def __init__(
        self,
        session_manager: SessionManager,
        timeout: float = settings.REQUEST_TIMEOUT,
    ):
        self.session_manager = session_manager
        self.timeout = timeout

    async def _get_authenticated_client(
        self,
        session_token: Optional[str] = None,
    ) -> httpx.AsyncClient:
        """Get an authenticated HTTP client."""
        session = await self.session_manager.get_session(session_token)
        if not session:
            raise ValueError(
                "No valid session available. Please login first or set GEOGUESSR_NCFA_COOKIE."
            )

        client = httpx.AsyncClient(timeout=self.timeout)
        client.cookies.set("_ncfa", session.ncfa_cookie, domain="www.geoguessr.com")
        return client

    @staticmethod
    def _get_base_url(endpoint: EndpointInfo) -> str:
        """Get the appropriate base URL for an endpoint."""
        return (
            settings.GAME_SERVER_URL
            if endpoint.use_game_server
            else settings.GEOGUESSR_API_URL
        )

    async def request(
        self,
        endpoint: EndpointInfo,
        session_token: Optional[str] = None,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        **kwargs,
    ) -> DynamicResponse:
        """
        Make a request to the GeoGuessr API.

        Args:
            endpoint: Endpoint info object
            session_token: Optional session token
            params: Query parameters
            json_data: JSON body for POST requests
            **kwargs: Additional arguments for httpx

        Returns:
            DynamicResponse with data and schema info
        """
        url = f"{self._get_base_url(endpoint)}{endpoint.path}"

        # Build params from endpoint builder if available
        if endpoint.params_builder and not params:
            params = endpoint.params_builder()

        logger.debug(f"{endpoint.method} {url}")

        import time
        start_time = time.time()

        async with await self._get_authenticated_client(session_token) as client:
            try:
                if endpoint.method == "GET":
                    response = await client.get(url, params=params, **kwargs)
                elif endpoint.method == "POST":
                    response = await client.post(url, json=json_data, params=params, **kwargs)
                else:
                    response = await client.request(
                        endpoint.method, url, json=json_data, params=params, **kwargs
                    )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Update schema registry
                        schema_registry.update_schema(
                            endpoint.path, data, response.status_code, endpoint.method
                        )
                    except Exception:
                        data = response.text
                else:
                    data = {"error": response.text, "status_code": response.status_code}
                    schema_registry.mark_unavailable(
                        endpoint.path, f"HTTP {response.status_code}", response.status_code
                    )

                return DynamicResponse(
                    data=data,
                    endpoint=endpoint.path,
                    status_code=response.status_code,
                    response_time_ms=response_time,
                )

            except httpx.TimeoutException:
                schema_registry.mark_unavailable(endpoint.path, "Request timeout")
                raise
            except Exception as e:
                schema_registry.mark_unavailable(endpoint.path, str(e))
                raise

    async def get(
        self,
        endpoint: EndpointInfo,
        session_token: Optional[str] = None,
        params: Optional[dict] = None,
        **kwargs,
    ) -> DynamicResponse:
        """Make a GET request."""
        return await self.request(endpoint, session_token, params=params, **kwargs)

    async def post(
        self,
        endpoint: EndpointInfo,
        session_token: Optional[str] = None,
        json_data: Optional[dict] = None,
        **kwargs,
    ) -> DynamicResponse:
        """Make a POST request."""
        return await self.request(endpoint, session_token, json_data=json_data, **kwargs)

    async def get_raw(
        self,
        path: str,
        session_token: Optional[str] = None,
        use_game_server: bool = False,
        params: Optional[dict] = None,
    ) -> DynamicResponse:
        """
        Make a raw GET request to any path.

        Useful for discovering new endpoints or accessing endpoints
        not yet defined in the registry.
        """
        endpoint = EndpointInfo(
            path=path,
            method="GET",
            use_game_server=use_game_server,
            description=f"Raw request to {path}",
        )
        return await self.get(endpoint, session_token, params)
