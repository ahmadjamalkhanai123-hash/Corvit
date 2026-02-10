"""Agent chat schemas per contracts/chat.md."""

from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class SourceCitation(BaseModel):
    collection: str
    document: str
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None
    action_taken: str | None = None
    data: dict[str, Any] | None = None
    sources: list[SourceCitation] = []
    session_id: str | None = None
