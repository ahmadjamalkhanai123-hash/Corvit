"""Tests for ChromaDB vector store."""

import pytest

from src.vectordb.store import VectorStore


@pytest.fixture
def store():
    return VectorStore()


def test_vectordb_connection(store: VectorStore):
    assert store.client is not None


def test_four_collections_exist(store: VectorStore):
    collections = store.list_collections()
    names = {c.name for c in collections}
    assert "courses" in names
    assert "teachers" in names
    assert "infrastructure" in names
    assert "policies" in names


def test_documents_loaded(store: VectorStore):
    total = 0
    for col in store.list_collections():
        total += col.count()
    assert total == 20


def test_query_returns_relevant_results(store: VectorStore):
    results = store.query_collection("courses", query_texts=["networking certification"], n_results=2)
    assert results is not None
    docs = results.get("documents", [[]])[0]
    assert len(docs) > 0
    assert any("CCNA" in d or "network" in d.lower() for d in docs)


def test_query_all_collections(store: VectorStore):
    results = store.query_all_collections(query_texts=["What courses do you offer?"], n_results=2)
    assert len(results) > 0
    collections_hit = {r["collection"] for r in results}
    assert "courses" in collections_hit
