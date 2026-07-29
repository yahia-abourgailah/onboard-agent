"""Environment-aware application configuration.

Config is loaded from environment variables (12-factor). Each deployment
environment — development, staging, production — supplies its own values via
the platform's secret/variable store; nothing is hardcoded here.
"""

import os
from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py already sits at src/config.py, so go up one level to reach project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MAPS_JSON_PATH = DATA_DIR / "maps.json"
FLOOR_SVG_PATH = DATA_DIR / "floor.svg"

PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")


class Environment(StrEnum):
    """Deployment environment, one per long-lived branch."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings, validated at process startup."""

    model_config = SettingsConfigDict(
        # env_prefix is intentionally left off: OPENAI_API_KEY is a well-known name
        # the OpenAI/LangChain client also reads, so we keep it un-prefixed rather
        # than forcing ONBOARD_OPENAI_API_KEY. Env var names below map 1:1.
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="")
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="URL of the Qdrant vector store used for the knowledge base.",
    )
    API_TOKEN: str = Field(
        default="",
        description="Secret token clients must send in the Authorization header.",
    )
    RATE_LIMIT_ENABLED: bool = Field(default=False)
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=20)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60)
    METRICS_ENABLED: bool = Field(default=True)
    INPUT_GUARDRAIL_ENABLED: bool = Field(default=True)
    # Explicit CORS allow-list, empty by default (no cross-origin). Set per
    # environment, e.g. CORS_ALLOW_ORIGINS='["https://app.example.com"]'.
    cors_allow_origins: list[str] = Field(default_factory=list)
    # LangSmith tracing (from the DB/agent PR); all optional and off by default.
    LANGSMITH_TRACING: bool = Field(default=False)
    LANGSMITH_API_KEY: str = Field(default="")
    LANGSMITH_PROJECT: str = Field(default="")
    LANGSMITH_ENDPOINT: str = Field(default="")

    POSTGRES_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        description="URL of the Postgres database used for persistent state.",
    )
    ALLOW_UNAUTHENTICATED: bool = Field(
        default=False,
        description=(
            "Allow unauthenticated requests when API_TOKEN is unset. Local development "
            "only, and only takes effect in the development environment. Defaults to "
            "False so a deployment that forgets to configure API_TOKEN fails closed."
        ),
    )

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


def get_settings() -> Settings:
    """Return validated settings; fail fast on invalid environment config."""
    return Settings()
