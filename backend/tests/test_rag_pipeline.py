"""Tests for RAG pipeline."""

from unittest.mock import AsyncMock

import pytest

from src.llm.base import LLMResponse
from src.rag.pipeline import RAGPipeline
from src.rag.prompts import build_context_from_results, build_system_prompt
from src.vectordb.store import VectorStore


def test_build_system_prompt_with_context():
    prompt = build_system_prompt("Some context about courses")
    assert "Corvit Systems" in prompt
    assert "Some context about courses" in prompt


def test_build_system_prompt_without_context():
    prompt = build_system_prompt("")
    assert "Corvit Systems" in prompt


def test_build_context_from_results():
    results = [
        {"collection": "courses", "document": "CCNA course info"},
        {"collection": "policies", "document": "Attendance policy info"},
    ]
    context = build_context_from_results(results)
    assert "courses" in context
    assert "CCNA" in context
    assert "policies" in context


@pytest.mark.asyncio
async def test_rag_pipeline_query_with_sources():
    """Test the full RAG pipeline with a mock LLM."""
    store = VectorStore()

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = LLMResponse(
        content="We offer CCNA, CEH, AI/ML, AWS, and Web Development courses.",
        model="test-model",
        usage={"prompt_tokens": 100, "completion_tokens": 20},
    )

    pipeline = RAGPipeline(store=store, llm=mock_llm, n_results=3)
    response = await pipeline.query("What courses do you offer?")

    assert response.answer != ""
    assert "course" in response.answer.lower() or "CCNA" in response.answer
    assert len(response.sources) > 0
    assert response.model == "test-model"
    mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_rag_pipeline_includes_source_citations():
    """Verify sources are included in the response."""
    store = VectorStore()
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = LLMResponse(content="Answer", model="test", usage={})

    pipeline = RAGPipeline(store=store, llm=mock_llm, n_results=2)
    response = await pipeline.query("Tell me about the AI course")

    assert len(response.sources) > 0
    for source in response.sources:
        assert source.collection in ("courses", "teachers", "infrastructure", "policies")
        assert source.document != ""
