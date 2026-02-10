"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM provider is reachable."""
        ...
