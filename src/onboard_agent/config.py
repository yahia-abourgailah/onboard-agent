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
        env_prefix="ONBOARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


def get_settings() -> Settings:
    """Return validated settings; fail fast on invalid environment config."""
    return Settings()
