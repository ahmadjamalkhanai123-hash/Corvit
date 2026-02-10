from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://corvit:corvit123@localhost:5432/corvit_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Ollama / LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    llm_provider: str = "ollama"

    # JWT Auth
    jwt_secret: str = "corvit-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Vector DB
    chroma_db_path: str = "src/vectordb/chroma_db"

    # App
    debug: bool = True
    app_name: str = "Corvit Agentic System"
    api_prefix: str = "/api"


def get_settings() -> Settings:
    return Settings()
