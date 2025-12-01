"""
Module for GeoGuessr dynamic HTTP client.

The module encapsulates the HTTP client for interacting with the
GeoGuessr API, including features such as authentication handling,
response schema tracking, retry logic, and integrated monitoring.

Classes:
- GeoGuessrClient: The main HTTP client for communicating with the GeoGuessr API.
"""

import logging

import httpx

from ..auth import get_current_user_context
from ..auth.session import SessionManager
from ..config import settings
from ..monitoring.schema.schema_registry import schema_registry
from .dynamic_response import DynamicResponse
from .endpoints import EndpointInfo

logger = logging.getLogger(__name__)


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
        session_token: str | None = None,
    ) -> httpx.AsyncClient:
        """
        Get an authenticated HTTP client.

        In multi-user mode, if no session_token is provided, uses the current user's context
        to get their session automatically.
        """
        # Try to get session from current user context (multi-user mode)
        user_context = get_current_user_context()
        if user_context and user_context.is_authenticated:
            # Use the session from the user's context
            session = user_context.session
        else:
            # Fall back to session manager (legacy mode or no user context)
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
        return settings.GAME_SERVER_URL if endpoint.use_game_server else settings.GEOGUESSR_API_URL

    async def request(
        self,
        endpoint: EndpointInfo,
        session_token: str | None = None,
        params: dict | None = None,
        json_data: dict | None = None,
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
        session_token: str | None = None,
        params: dict | None = None,
        **kwargs,
    ) -> DynamicResponse:
        """Make a GET request."""
        return await self.request(endpoint, session_token, params=params, **kwargs)

    async def post(
        self,
        endpoint: EndpointInfo,
        session_token: str | None = None,
        json_data: dict | None = None,
        **kwargs,
    ) -> DynamicResponse:
        """Make a POST request."""
        return await self.request(endpoint, session_token, json_data=json_data, **kwargs)

    async def get_raw(
        self,
        path: str,
        session_token: str | None = None,
        use_game_server: bool = False,
        params: dict | None = None,
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
