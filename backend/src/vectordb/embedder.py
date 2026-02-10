"""Document embedding pipeline using ChromaDB default embeddings."""

import json
from pathlib import Path
from typing import Any

from src.vectordb.store import VectorStore


def load_corvit_data(data_path: str | None = None) -> dict[str, Any]:
    """Load corvit_data.json from the default or specified path."""
    if data_path is None:
        data_path = str(Path(__file__).parent / "data" / "corvit_data.json")
    with open(data_path) as f:
        return json.load(f)


def embed_documents(
    store: VectorStore,
    collection_name: str,
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
    ids: list[str] | None = None,
) -> int:
    """Embed documents into a ChromaDB collection.

    Uses ChromaDB's default embedding function (all-MiniLM-L6-v2).
    Returns the number of documents added.
    """
    collection = store.get_or_create_collection(collection_name)
    if ids is None:
        ids = [f"{collection_name}-{i}" for i in range(len(documents))]
    if metadatas is None:
        metadatas = [{"source": collection_name} for _ in documents]

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    return len(documents)
