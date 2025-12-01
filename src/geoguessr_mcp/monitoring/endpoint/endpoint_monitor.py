"""
Monitors GeoGuessr API endpoints for availability and schema changes.

This module is responsible for monitoring a set of known GeoGuessr API endpoints
to ensure their availability and detect schema changes. It periodically checks
each endpoint, logs relevant details about its status, and updates a schema
registry when necessary.

Classes:
    EndpointMonitor: Manages periodic checks of API endpoints, updates schema
    registry, and logs activity.
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

import httpx

from ...config import settings
from ..schema.schema_registry import SchemaRegistry, schema_registry
from .endpoint_definition import EndpointDefinition
from .endpoint_monitoring_result import MonitoringResult

logger = logging.getLogger(__name__)

# Known GeoGuessr API endpoints to monitor
MONITORED_ENDPOINTS = [
    # Profile endpoints
    EndpointDefinition(
        path="/v3/profiles",
        description="Current user profile",
    ),
    EndpointDefinition(
        path="/v3/profiles/stats",
        description="User statistics",
    ),
    EndpointDefinition(
        path="/v4/stats/me",
        description="Extended user statistics",
    ),
    EndpointDefinition(
        path="/v3/profiles/achievements",
        description="User achievements",
    ),
    EndpointDefinition(
        path="/v3/profiles/maps",
        description="User's custom maps",
    ),
    # Game endpoints
    EndpointDefinition(
        path="/v3/social/events/unfinishedgames",
        description="Unfinished games",
    ),
    # Social endpoints
    EndpointDefinition(
        path="/v4/feed/private",
        params={"count": 10, "page": 0},
        description="Private activity feed",
    ),
    EndpointDefinition(
        path="/v3/social/friends/summary",
        description="Friends summary",
    ),
    EndpointDefinition(
        path="/v3/social/badges/unclaimed",
        description="Unclaimed badges",
    ),
    EndpointDefinition(
        path="/v3/social/maps/browse/personalized",
        description="Personalized map recommendations",
    ),
    # Competitive endpoints
    EndpointDefinition(
        path="/v4/seasons/active/stats",
        description="Active season statistics",
    ),
    # Explorer endpoints
    EndpointDefinition(
        path="/v3/explorer",
        description="Explorer mode progress",
    ),
    # Objectives endpoints
    EndpointDefinition(
        path="/v4/objectives",
        description="Current objectives",
    ),
    EndpointDefinition(
        path="/v4/objectives/unclaimed",
        description="Unclaimed objective rewards",
    ),
    # Subscription endpoints
    EndpointDefinition(
        path="/v3/subscriptions",
        description="Subscription information",
    ),
    # Challenge endpoints
    EndpointDefinition(
        path="/v3/challenges/daily-challenges/today",
        description="Today's daily challenge",
    ),
    # Game server endpoints
    EndpointDefinition(
        path="/tournaments",
        use_game_server=True,
        description="Tournament information",
    ),
]


class EndpointMonitor:
    """
    Monitors API endpoints for availability and schema changes.

    This class runs periodic checks on all known endpoints, updating the
    schema registry with any changes detected.
    """

    def __init__(
        self,
        registry: SchemaRegistry | None = None,
        ncfa_cookie: str | None = None,
    ):
        self.registry = registry or schema_registry
        self.ncfa_cookie = ncfa_cookie or settings.DEFAULT_NCFA_COOKIE
        self.results: list[MonitoringResult] = []
        self._running = False
        self._task: asyncio.Task | None = None

    async def check_endpoint(
        self,
        endpoint: EndpointDefinition,
        client: httpx.AsyncClient,
    ) -> MonitoringResult:
        """
        Check a single endpoint and update its schema.

        Args:
            endpoint: The endpoint definition to check
            client: HTTP client to use

        Returns:
            MonitoringResult with check details
        """
        base_url = (
            settings.GAME_SERVER_URL if endpoint.use_game_server else settings.GEOGUESSR_API_URL
        )
        url = f"{base_url}{endpoint.path}"

        start_time = datetime.now(UTC)

        try:
            response = await client.request(
                endpoint.method,
                url,
                params=endpoint.params if endpoint.params else None,
                timeout=settings.REQUEST_TIMEOUT,
            )

            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

            if response.status_code == 200:
                try:
                    data = response.json()
                    schema, changed = self.registry.update_schema(
                        endpoint.path,
                        data,
                        response.status_code,
                        endpoint.method,
                    )
                    return MonitoringResult(
                        endpoint=endpoint.path,
                        is_available=True,
                        response_code=response.status_code,
                        response_time_ms=response_time,
                        schema_changed=changed,
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse response from {endpoint.path}: {e}")
                    return MonitoringResult(
                        endpoint=endpoint.path,
                        is_available=True,
                        response_code=response.status_code,
                        response_time_ms=response_time,
                        schema_changed=False,
                        error_message=f"Parse error: {str(e)}",
                    )
            else:
                self.registry.mark_unavailable(
                    endpoint.path,
                    f"HTTP {response.status_code}",
                    response.status_code,
                )
                return MonitoringResult(
                    endpoint=endpoint.path,
                    is_available=False,
                    response_code=response.status_code,
                    response_time_ms=response_time,
                    schema_changed=False,
                    error_message=f"HTTP {response.status_code}",
                )

        except httpx.TimeoutException:
            self.registry.mark_unavailable(endpoint.path, "Timeout")
            return MonitoringResult(
                endpoint=endpoint.path,
                is_available=False,
                response_code=0,
                response_time_ms=settings.REQUEST_TIMEOUT * 1000,
                schema_changed=False,
                error_message="Request timeout",
            )
        except Exception as e:
            self.registry.mark_unavailable(endpoint.path, str(e))
            return MonitoringResult(
                endpoint=endpoint.path,
                is_available=False,
                response_code=0,
                response_time_ms=0,
                schema_changed=False,
                error_message=str(e),
            )

    async def run_full_check(self) -> list[MonitoringResult]:
        """
        Run a full check of all monitored endpoints.

        Returns:
            List of monitoring results for all endpoints
        """
        if not self.ncfa_cookie:
            logger.warning("No authentication cookie available for monitoring")
            return []

        results = []

        async with httpx.AsyncClient() as client:
            client.cookies.set("_ncfa", self.ncfa_cookie, domain="www.geoguessr.com")

            for endpoint in MONITORED_ENDPOINTS:
                try:
                    result = await self.check_endpoint(endpoint, client)
                    results.append(result)

                    status = "✓" if result.is_available else "✗"
                    changed = " [SCHEMA CHANGED]" if result.schema_changed else ""
                    logger.info(
                        f"{status} {endpoint.path}: "
                        f"{result.response_code} ({result.response_time_ms:.0f}ms){changed}"
                    )

                    # Small delay between requests to avoid rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error checking {endpoint.path}: {e}")
                    results.append(
                        MonitoringResult(
                            endpoint=endpoint.path,
                            is_available=False,
                            response_code=0,
                            response_time_ms=0,
                            schema_changed=False,
                            error_message=str(e),
                        )
                    )

        self.results = results
        return results

    async def start_periodic_monitoring(self) -> None:
        """Start the periodic monitoring background task."""
        if self._running:
            logger.warning("Monitoring already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info(
            f"Started periodic monitoring (interval: {settings.MONITORING_INTERVAL_HOURS}h)"
        )

    async def stop_monitoring(self) -> None:
        """Stop the periodic monitoring background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Stopped periodic monitoring")

    async def _monitoring_loop(self) -> None:
        """Background loop for periodic monitoring."""
        while self._running:
            try:
                logger.info("Running scheduled endpoint check...")
                await self.run_full_check()

                # Wait for next check interval
                await asyncio.sleep(settings.MONITORING_INTERVAL_HOURS * 3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Wait a bit before retrying on error
                await asyncio.sleep(60)

    def get_monitoring_report(self) -> dict:
        """
        Generate a monitoring report for all endpoints.

        Returns:
            Dictionary with monitoring summary and details
        """
        if not self.results:
            return {
                "status": "no_data",
                "message": "No monitoring data available. Run a check first.",
            }

        available = [r for r in self.results if r.is_available]
        unavailable = [r for r in self.results if not r.is_available]
        changed = [r for r in self.results if r.schema_changed]

        avg_response_time = (
            sum(r.response_time_ms for r in available) / len(available) if available else 0
        )

        return {
            "status": "ok" if len(unavailable) == 0 else "degraded",
            "summary": {
                "total_endpoints": len(self.results),
                "available": len(available),
                "unavailable": len(unavailable),
                "schema_changes": len(changed),
                "average_response_time_ms": round(avg_response_time, 2),
                "last_check": self.results[0].timestamp.isoformat() if self.results else None,
            },
            "available_endpoints": [
                {
                    "endpoint": r.endpoint,
                    "response_code": r.response_code,
                    "response_time_ms": round(r.response_time_ms, 2),
                    "schema_changed": r.schema_changed,
                }
                for r in available
            ],
            "unavailable_endpoints": [
                {
                    "endpoint": r.endpoint,
                    "error": r.error_message,
                    "response_code": r.response_code,
                }
                for r in unavailable
            ],
            "schema_changes": [
                {
                    "endpoint": r.endpoint,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in changed
            ],
        }


# Global monitor instance
endpoint_monitor = EndpointMonitor()
