"""
This module defines a data structure representing the result of monitoring a
network endpoint.

It contains the necessary details to capture the status and performance of
an endpoint, including its availability, response time, and any errors encountered.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional


@dataclass
class MonitoringResult:
    """Result of monitoring an endpoint."""

    endpoint: str
    is_available: bool
    response_code: int
    response_time_ms: float
    schema_changed: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
