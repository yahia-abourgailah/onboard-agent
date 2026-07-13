"""Unit tests for environment configuration."""

import pytest

from onboard_agent.config import Environment, Settings


def test_defaults_to_development() -> None:
    settings = Settings()
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.is_production is False


def test_reads_environment_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONBOARD_ENVIRONMENT", "production")
    settings = Settings()
    assert settings.environment is Environment.PRODUCTION
    assert settings.is_production is True


def test_rejects_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONBOARD_ENVIRONMENT", "qa")
    with pytest.raises(ValueError):
        Settings()
