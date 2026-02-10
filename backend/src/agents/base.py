"""Abstract base agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    """Context passed to agents for processing."""
    user_id: str | None = None
    user_role: str | None = None
    session_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Standard response from any agent."""
    reply: str
    intent: str | None = None
    action_taken: str | None = None
    data: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    session_id: str | None = None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    async def process_message(
        self, message: str, context: AgentContext | None = None
    ) -> AgentResponse:
        """Process a user message and return a response."""
        ...
