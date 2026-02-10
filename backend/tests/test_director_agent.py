"""Tests for Director Agent: intent classification, response format."""

import pytest

from src.agents.director.router import IntentRouter, VALID_INTENTS


class MockLLMProvider:
    """Mock LLM provider that returns predetermined intent."""

    def __init__(self, intent: str = "general"):
        self._intent = intent

    async def generate(self, messages, temperature=0.7, max_tokens=1024):
        from src.llm.base import LLMResponse
        return LLMResponse(content=self._intent, model="mock", usage={})

    async def is_available(self):
        return True


@pytest.mark.asyncio
async def test_intent_classification_course_inquiry():
    """Course-related messages should classify as course_inquiry."""
    router = IntentRouter(MockLLMProvider("course_inquiry"))
    intent = await router.classify("What courses do you offer?")
    assert intent == "course_inquiry"


@pytest.mark.asyncio
async def test_intent_classification_attendance():
    """Attendance-related messages should classify as attendance_query."""
    router = IntentRouter(MockLLMProvider("attendance_query"))
    intent = await router.classify("What is my attendance?")
    assert intent == "attendance_query"


@pytest.mark.asyncio
async def test_intent_classification_fee():
    """Fee-related messages should classify as fee_query."""
    router = IntentRouter(MockLLMProvider("fee_query"))
    intent = await router.classify("How much do I owe?")
    assert intent == "fee_query"


@pytest.mark.asyncio
async def test_intent_classification_enrollment():
    """Enrollment messages should classify as enrollment."""
    router = IntentRouter(MockLLMProvider("enrollment"))
    intent = await router.classify("I want to enroll in CCNA")
    assert intent == "enrollment"


@pytest.mark.asyncio
async def test_intent_classification_complaint():
    """Complaint messages should classify as complaint."""
    router = IntentRouter(MockLLMProvider("complaint"))
    intent = await router.classify("I have a complaint about the teacher")
    assert intent == "complaint"


@pytest.mark.asyncio
async def test_intent_classification_fallback():
    """Unknown intent should fall back to general."""
    router = IntentRouter(MockLLMProvider("something_unknown"))
    intent = await router.classify("Random message")
    assert intent == "general"


@pytest.mark.asyncio
async def test_valid_intents_complete():
    """All 9 intent categories should be present."""
    expected = {
        "course_inquiry", "enrollment", "fee_query",
        "attendance_query", "counseling", "complaint",
        "general", "class_related", "lab_related",
    }
    assert VALID_INTENTS == expected


def test_agent_response_structure():
    """AgentResponse should have all required fields."""
    from src.agents.base import AgentResponse

    resp = AgentResponse(
        reply="Test response",
        intent="course_inquiry",
        action_taken=None,
        data=None,
        sources=[{"collection": "courses", "document": "test", "relevance_score": 0.9}],
        session_id="test-session",
    )
    assert resp.reply == "Test response"
    assert resp.intent == "course_inquiry"
    assert len(resp.sources) == 1


def test_chat_request_schema():
    """ChatRequest schema validation."""
    from src.api.schemas.agent import ChatRequest

    req = ChatRequest(message="Hello", session_id="test-123")
    assert req.message == "Hello"
    assert req.session_id == "test-123"

    req2 = ChatRequest(message="Hello")
    assert req2.session_id is None


def test_chat_response_schema():
    """ChatResponse schema validation."""
    from src.api.schemas.agent import ChatResponse, SourceCitation

    resp = ChatResponse(
        reply="Corvit offers 5 courses",
        intent="course_inquiry",
        sources=[SourceCitation(collection="courses", document="test", relevance_score=0.9)],
        session_id="test-123",
    )
    assert resp.reply == "Corvit offers 5 courses"
    assert resp.intent == "course_inquiry"
    assert len(resp.sources) == 1
