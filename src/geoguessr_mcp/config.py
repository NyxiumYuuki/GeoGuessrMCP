"""Configuration management for GeoGuessr MCP Server."""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # MCP Server Configuration
    HOST: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8000")))
    TRANSPORT: str = field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "streamable-http"))

    # GeoGuessr API Configuration
    GEOGUESSR_DOMAIN_NAME: str = "geoguessr.com"
    GEOGUESSR_API_URL: str = "https://www.geoguessr.com/api"
    GAME_SERVER_URL: str = "https://game-server.geoguessr.com/api"
    DEFAULT_NCFA_COOKIE: str | None = field(
        default_factory=lambda: os.getenv("GEOGUESSR_NCFA_COOKIE")
    )

    # API Monitoring Configuration
    MONITORING_ENABLED: bool = field(
        default_factory=lambda: os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    )
    MONITORING_INTERVAL_HOURS: int = field(
        default_factory=lambda: int(os.getenv("MONITORING_INTERVAL_HOURS", "24"))
    )
    SCHEMA_CACHE_DIR: str = field(
        default_factory=lambda: os.getenv("SCHEMA_CACHE_DIR", "./data/schemas")
    )

    # Authentication Configuration
    MCP_AUTH_ENABLED: bool = field(
        default_factory=lambda: os.getenv("MCP_AUTH_ENABLED", "false").lower() == "true"
    )
    MCP_API_KEYS: str | None = field(default_factory=lambda: os.getenv("MCP_API_KEYS"))

    # Logging Configuration
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Request Configuration
    REQUEST_TIMEOUT: float = field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    )
    MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.PORT < 1 or self.PORT > 65535:
            raise ValueError(f"Invalid port number: {self.PORT}")
        if self.MONITORING_INTERVAL_HOURS < 1:
            raise ValueError("Monitoring interval must be at least 1 hour")
        if self.MCP_AUTH_ENABLED and not self.MCP_API_KEYS:
            raise ValueError("MCP_AUTH_ENABLED is true but MCP_API_KEYS is not set")

    def get_api_keys(self) -> set[str]:
        """Parse and return the set of valid API keys."""
        if not self.MCP_API_KEYS:
            return set()
        # Support comma-separated API keys
        return {key.strip() for key in self.MCP_API_KEYS.split(",") if key.strip()}


settings = Settings()
