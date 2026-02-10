import os

import pytest

from src.config.settings import Settings, get_settings


def test_settings_loads_defaults():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
    )
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.ollama_model == "qwen2.5:7b"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expire_minutes == 480
    assert settings.debug is True


def test_settings_overrides_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://custom:pw@db:5432/custom")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/1")
    monkeypatch.setenv("JWT_SECRET", "super-secret")
    monkeypatch.setenv("DEBUG", "false")

    settings = Settings(_env_file=None)
    assert settings.database_url == "postgresql+asyncpg://custom:pw@db:5432/custom"
    assert settings.redis_url == "redis://redis:6379/1"
    assert settings.jwt_secret == "super-secret"
    assert settings.debug is False


def test_get_settings_returns_instance():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "Corvit Agentic System"
