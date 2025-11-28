"""
Definition of API endpoint data structure to monitor.

This module provides the `EndpointDefinition` class to encapsulate necessary
details about an API endpoint, such as its path, request method, authentication
requirement, and additional parameters.
"""

from dataclasses import dataclass, field


@dataclass
class EndpointDefinition:
    """Definition of an API endpoint to monitor."""

    path: str
    method: str = "GET"
    requires_auth: bool = True
    use_game_server: bool = False
    params: dict = field(default_factory=dict)
    description: str = ""
