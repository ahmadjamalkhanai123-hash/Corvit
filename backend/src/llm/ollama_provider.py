"""Ollama LLM provider implementation."""

import httpx

from src.config.settings import get_settings
from src.llm.base import LLMMessage, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama via HTTP API."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        settings = get_settings()
        self._base_url = base_url or settings.ollama_base_url
        self._model = model or settings.ollama_model

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        return LLMResponse(content=content, model=self._model, usage=usage)

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    return any(self._model in m for m in models)
            return False
        except Exception:
            return False
