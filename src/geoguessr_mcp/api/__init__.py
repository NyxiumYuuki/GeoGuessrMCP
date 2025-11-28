"""API client module for GeoGuessr communication."""

from .client import DynamicResponse, GeoGuessrClient
from .endpoints import EndpointBuilder, EndpointInfo, Endpoints

__all__ = [
    "GeoGuessrClient",
    "DynamicResponse",
    "Endpoints",
    "EndpointInfo",
    "EndpointBuilder",
]
