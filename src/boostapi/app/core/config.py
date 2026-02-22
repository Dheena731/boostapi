"""Application configuration via pydantic-settings."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    BoostAPI configuration — all values are readable from environment variables
    or a ``.env`` file automatically.

    Example::

        # .env
        POSTGRES_DB=mydb
        SECRET_KEY=super-secret

        # Python
        from boostapi.app.core.config import Settings
        s = Settings()
        print(s.DATABASE_URL)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Project ───────────────────────────────────────────────
    PROJECT_NAME: str = "BoostAPI"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Database ──────────────────────────────────────────────
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "boostapi"
    DATABASE_URL: str = ""

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 300  # seconds

    # ── Auth ──────────────────────────────────────────────────
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @model_validator(mode="before")
    @classmethod
    def build_database_url(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Auto-build DATABASE_URL from individual Postgres parts if not set."""
        if not values.get("DATABASE_URL"):
            server = values.get("POSTGRES_SERVER", "localhost")
            port = values.get("POSTGRES_PORT", 5432)
            user = values.get("POSTGRES_USER", "postgres")
            password = values.get("POSTGRES_PASSWORD", "password")
            db = values.get("POSTGRES_DB", "boostapi")
            values["DATABASE_URL"] = (
                f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"
            )
        return values

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Accept a JSON string or a list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (singleton)."""
    return Settings()


# Module-level singleton — safe to import directly
settings: Settings = get_settings()
