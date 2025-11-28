"""
HTTP client for Geoguessr API communication.
"""

import httpx
import logging
from typing import Optional
from ..auth.session import SessionManager
from .endpoints import EndpointBuilder, get_endpoint_info

from ..config import settings

logger = logging.getLogger(__name__)


class GeoguessrClient:
    """
    Wrapper for Geoguessr API HTTP communication.

    This client automatically handles:
    - Authentication via session manager
    - Endpoint routing (main API vs. game server)
    - Error handling and retries
    - Logging and debugging
    """

    def __init__(
        self,
        session_manager: SessionManager,
        base_url: str = settings.GEOGUESSR_API_URL,
        game_server_url: str = settings.GAME_SERVER_URL,
        timeout: float = 30.0
    ):
        """
        Initialize the Geoguessr API client.

        Args:
            session_manager: Session manager for authentication
            base_url: Base URL for Geoguessr API
            game_server_url: URL for game server API
            timeout: Request timeout in seconds
        """
        self.session_manager = session_manager
        self.base_url = base_url
        self.game_server_url = game_server_url
        self.timeout = timeout

    async def get_authenticated_client(
        self,
        session_token: Optional[str] = None
    ) -> httpx.AsyncClient:
        """
        Get an authenticated async HTTP client.

        Args:
            session_token: Optional session token for authentication

        Returns:
            Authenticated httpx.AsyncClient

        Raises:
            ValueError: If no valid session is available
        """
        session = await self.session_manager.get_session(session_token)
        if not session:
            raise ValueError(
                "No valid session available. Please:\n"
                "1. Use login() to authenticate, or\n"
                "2. Set GEOGUESSR_NCFA_COOKIE environment variable"
            )

        client = httpx.AsyncClient(timeout=self.timeout)
        client.cookies.set(
            "_ncfa",
            session.ncfa_cookie,
            domain="www.geoguessr.com"
        )
        return client

    def _get_base_url(self, endpoint: str, use_game_server: Optional[bool] = None) -> str:
        """
        Determine the correct base URL for an endpoint.

        Args:
            endpoint: API endpoint
            use_game_server: Explicitly set game server usage, or auto-detect

        Returns:
            Appropriate base URL
        """
        if use_game_server is None:
            # Auto-detect based on endpoint
            use_game_server = EndpointBuilder.is_game_server_endpoint(endpoint)

        return self.game_server_url if use_game_server else self.base_url

    async def get(
        self,
        endpoint: str,
        session_token: Optional[str] = None,
        use_game_server: Optional[bool] = None,
        params: Optional[dict] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a GET request to the Geoguessr API.

        Args:
            endpoint: API endpoint (e.g., "/v3/profiles")
            session_token: Optional session token
            use_game_server: Whether to use game server URL (auto-detected if None)
            params: Query parameters
            **kwargs: Additional arguments to pass to httpx.get

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        base = self._get_base_url(endpoint, use_game_server)
        url = f"{base}{endpoint}"

        # Get endpoint metadata for logging
        metadata = get_endpoint_info(endpoint)
        logger.debug(
            f"GET {url} - {metadata.get('description', 'Unknown endpoint')}"
        )

        async with await self.get_authenticated_client(session_token) as client:
            response = await client.get(url, params=params, **kwargs)
            response.raise_for_status()
            logger.debug(f"GET {url} - Success ({response.status_code})")
            return response

    async def post(
        self,
        endpoint: str,
        session_token: Optional[str] = None,
        use_game_server: Optional[bool] = None,
        json_data: Optional[dict] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a POST request to the Geoguessr API.

        Args:
            endpoint: API endpoint
            session_token: Optional session token
            use_game_server: Whether to use game server URL (auto-detected if None)
            json_data: JSON data to send
            **kwargs: Additional arguments to pass to httpx.post

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        base = self._get_base_url(endpoint, use_game_server)
        url = f"{base}{endpoint}"

        metadata = get_endpoint_info(endpoint)
        logger.debug(
            f"POST {url} - {metadata.get('description', 'Unknown endpoint')}"
        )

        async with await self.get_authenticated_client(session_token) as client:
            response = await client.post(url, json=json_data, **kwargs)
            response.raise_for_status()
            logger.debug(f"POST {url} - Success ({response.status_code})")
            return response

    async def request(
        self,
        method: str,
        endpoint: str,
        session_token: Optional[str] = None,
        use_game_server: Optional[bool] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a generic HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            session_token: Optional session token
            use_game_server: Whether to use game server URL
            **kwargs: Additional arguments to pass to httpx

        Returns:
            httpx.Response
        """
        base = self._get_base_url(endpoint, use_game_server)
        url = f"{base}{endpoint}"

        async with await self.get_authenticated_client(session_token) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
