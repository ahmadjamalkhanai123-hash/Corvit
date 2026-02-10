"""LLM provider factory."""

from src.config.settings import Settings, get_settings
from src.llm.base import LLMProvider
from src.llm.ollama_provider import OllamaProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Create an LLM provider based on settings.

    Currently supports:
    - "ollama" (default): OllamaProvider
    Future: "claude", "openai", etc.
    """
    if settings is None:
        settings = get_settings()

    provider_name = settings.llm_provider.lower()

    if provider_name == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    raise ValueError(f"Unknown LLM provider: {provider_name}. Supported: ollama")
