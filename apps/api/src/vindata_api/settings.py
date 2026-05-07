"""Strongly-typed settings, hydrated from environment.

Single ``Settings`` instance used as a FastAPI dependency; never import the
class itself in routers. The instance is cached at import time after process
start, so reads inside hot paths are free.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, all keyed under the ``VINDATA_API_`` prefix."""

    model_config = SettingsConfigDict(
        env_prefix="VINDATA_API_",
        env_file=None,  # set by docker-compose; explicit env in tests.
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "0.0.0.0"  # noqa: S104 — bound inside a container only
    port: int = 8000
    log_level: Annotated[str, Field(pattern="^(debug|info|warning|error)$")] = "info"
    database_url: str = "postgresql+asyncpg://vindata:vindata@postgres:5432/vindata"
    cors_origins: str = "http://localhost:5173"
    title: str = "VinData API"
    version: str = "0.0.1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton accessor; safe to call repeatedly."""
    return Settings()
