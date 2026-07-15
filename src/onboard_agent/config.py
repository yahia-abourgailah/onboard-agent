"""Environment-aware application configuration.

Config is loaded from environment variables (12-factor). Each deployment
environment — development, staging, production — supplies its own values via
the platform's secret/variable store; nothing is hardcoded here.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# from pydantic import Field, field_validator
# from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment, one per long-lived branch."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings, validated at process startup."""

    model_config = SettingsConfigDict(
        # env_prefix="ONBOARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="")

    API_TOKEN: str = Field(
        default="",
        description="Secret token clients must send in the Authorization header.",
    )

    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        description="Comma-separated list of origins allowed to make credentialed "
        "CORS requests, e.g. https://app.example.com,https://staging.example.com",
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: str | list[str]) -> list[str]:
        """Allow ALLOWED_ORIGINS to be set as a comma-separated string in .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


def get_settings() -> Settings:
    """Return validated settings; fail fast on invalid environment config."""
    return Settings()
