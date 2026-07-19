"""Environment-aware application configuration.

Config is loaded from environment variables (12-factor). Each deployment
environment — development, staging, production — supplies its own values via
the platform's secret/variable store; nothing is hardcoded here.
"""

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Explicit CORS allow-list, empty by default (no cross-origin). Set per
    # environment, e.g. CORS_ALLOW_ORIGINS='["https://app.example.com"]'.
    cors_allow_origins: list[str] = Field(default_factory=list)
    # LangSmith tracing (from the DB/agent PR); all optional and off by default.
    LANGSMITH_TRACING: bool = Field(default=False)
    LANGSMITH_API_KEY: str = Field(default="")
    LANGSMITH_PROJECT: str = Field(default="")
    LANGSMITH_ENDPOINT: str = Field(default="")


    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


def get_settings() -> Settings:
    """Return validated settings; fail fast on invalid environment config."""
    return Settings()
