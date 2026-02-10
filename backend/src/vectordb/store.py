"""ChromaDB vector store interface."""

from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src.config.settings import get_settings


class VectorStore:
    """Interface to ChromaDB for document storage and retrieval."""

    def __init__(self, path: str | None = None):
        settings = get_settings()
        self._path = path or settings.chroma_db_path
        self._client = chromadb.PersistentClient(path=self._path)

    @property
    def client(self) -> chromadb.ClientAPI:
        return self._client

    def get_or_create_collection(self, name: str) -> Collection:
        return self._client.get_or_create_collection(name=name)

    def get_collection(self, name: str) -> Collection:
        return self._client.get_collection(name=name)

    def list_collections(self) -> list[Collection]:
        return self._client.list_collections()

    def query_collection(
        self,
        collection_name: str,
        query_texts: list[str],
        n_results: int = 5,
    ) -> dict[str, Any]:
        collection = self.get_collection(collection_name)
        return collection.query(query_texts=query_texts, n_results=n_results)

    def query_all_collections(
        self,
        query_texts: list[str],
        n_results: int = 3,
    ) -> list[dict[str, Any]]:
        results = []
        for col in self.list_collections():
            try:
                r = col.query(query_texts=query_texts, n_results=n_results)
                for i, doc_list in enumerate(r.get("documents", [[]])):
                    for j, doc in enumerate(doc_list):
                        meta = {}
                        if r.get("metadatas") and r["metadatas"][i]:
                            meta = r["metadatas"][i][j] or {}
                        distance = None
                        if r.get("distances") and r["distances"][i]:
                            distance = r["distances"][i][j]
                        results.append({
                            "collection": col.name,
                            "document": doc,
                            "metadata": meta,
                            "distance": distance,
                        })
            except Exception:
                continue
        results.sort(key=lambda x: x.get("distance") or float("inf"))
        return results
