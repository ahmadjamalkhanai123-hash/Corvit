"""
Application Configuration
=========================

Uses pydantic-settings for environment-based configuration.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Create a .env file in the project root:
        APP_NAME=FastAPI Skills Lab
        DEBUG=true
        DATABASE_URL=sqlite:///./app.db
        SECRET_KEY=your-secret-key
    """

    # Application
    app_name: str = "FastAPI Skills Lab"
    debug: bool = True
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./app.db"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.

    Using lru_cache ensures settings are only loaded once.
    """
    return Settings()


# Convenience access
settings = get_settings()
