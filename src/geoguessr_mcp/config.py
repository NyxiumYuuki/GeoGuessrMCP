"""Configuration management."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_PORT", "8000"))
    TRANSPORT: str = os.getenv("MCP_TRANSPORT", "streamable-http")
    GEOGUESSR_BASE_URL: str = "https://www.geoguessr.com/api"
    GAME_SERVER_URL: str = "https://game-server.geoguessr.com/api"
    DEFAULT_NCFA_COOKIE: str | None = os.getenv("GEOGUESSR_NCFA_COOKIE")


settings = Settings()
