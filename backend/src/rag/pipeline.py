"""RAG pipeline: query → vector search → LLM → answer with sources."""

from dataclasses import dataclass, field

from src.llm.base import LLMMessage, LLMProvider
from src.rag.prompts import build_context_from_results, build_system_prompt
from src.vectordb.store import VectorStore


@dataclass
class RAGSource:
    collection: str
    document: str
    metadata: dict = field(default_factory=dict)
    distance: float | None = None


@dataclass
class RAGResponse:
    answer: str
    sources: list[RAGSource]
    model: str


class RAGPipeline:
    """Query ChromaDB for context, inject into prompt, call LLM."""

    def __init__(self, store: VectorStore, llm: LLMProvider, n_results: int = 3):
        self._store = store
        self._llm = llm
        self._n_results = n_results

    async def query(self, question: str) -> RAGResponse:
        # 1. Retrieve relevant documents from all collections
        results = self._store.query_all_collections(
            query_texts=[question],
            n_results=self._n_results,
        )

        # 2. Build context from results
        context = build_context_from_results(results) if results else ""

        # 3. Build messages
        system_prompt = build_system_prompt(context)
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=question),
        ]

        # 4. Call LLM
        llm_response = await self._llm.generate(messages)

        # 5. Build sources
        sources = [
            RAGSource(
                collection=r["collection"],
                document=r["document"][:200],
                metadata=r.get("metadata", {}),
                distance=r.get("distance"),
            )
            for r in results
        ]

        return RAGResponse(
            answer=llm_response.content,
            sources=sources,
            model=llm_response.model,
        )
