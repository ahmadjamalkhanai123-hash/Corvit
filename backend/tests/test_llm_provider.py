"""Tests for LLM provider abstraction."""

import pytest

from src.config.settings import Settings
from src.llm.base import LLMMessage, LLMProvider, LLMResponse
from src.llm.factory import get_llm_provider
from src.llm.ollama_provider import OllamaProvider


def test_llm_provider_is_abstract():
    """LLMProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        LLMProvider()


def test_llm_message_creation():
    msg = LLMMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_llm_response_creation():
    resp = LLMResponse(content="Hi", model="test", usage={"prompt_tokens": 10})
    assert resp.content == "Hi"
    assert resp.model == "test"
    assert resp.usage["prompt_tokens"] == 10


def test_factory_creates_ollama_provider():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
        llm_provider="ollama",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, OllamaProvider)


def test_factory_rejects_unknown_provider():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
        llm_provider="unknown",
    )
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider(settings)


@pytest.mark.asyncio
async def test_ollama_is_available():
    """Test is_available returns bool (may be False if Ollama not running)."""
    provider = OllamaProvider()
    result = await provider.is_available()
    assert isinstance(result, bool)
