"""
Vector Database Abstraction
===========================

Unified interface for vector databases (ChromaDB, Pinecone, pgvector).
"""

from abc import ABC, abstractmethod
from typing import Any
import math

from ..core.config import settings


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None) -> list[str]:
        """Add documents to the store."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> bool:
        """Delete documents by IDs."""
        pass


class ChromaDBStore(VectorStore):
    """
    ChromaDB vector store.

    Requires: pip install chromadb
    """

    def __init__(self, collection_name: str = "default", persist_directory: str = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    def _init_client(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(self.collection_name)
        except ImportError:
            raise ImportError("chromadb package required: pip install chromadb")

    @property
    def collection(self):
        if self._collection is None:
            self._init_client()
        return self._collection

    def add(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None) -> list[str]:
        """Add documents."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        return ids

    def search(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        """Search documents."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filters
        )
        return [
            {"id": id, "text": doc, "metadata": meta, "distance": dist}
            for id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [{}] * len(results["ids"][0]),
                results["distances"][0] if results["distances"] else [0] * len(results["ids"][0])
            )
        ]

    def delete(self, ids: list[str]) -> bool:
        """Delete documents."""
        self.collection.delete(ids=ids)
        return True


class PineconeStore(VectorStore):
    """
    Pinecone vector store.

    Requires: pip install pinecone-client
    """

    def __init__(self, index_name: str, api_key: str = None, environment: str = None):
        self.index_name = index_name
        self.api_key = api_key or getattr(settings, 'pinecone_api_key', '')
        self.environment = environment or getattr(settings, 'pinecone_environment', '')
        self._index = None

    def _init_client(self):
        """Initialize Pinecone."""
        try:
            import pinecone
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self._index = pinecone.Index(self.index_name)
        except ImportError:
            raise ImportError("pinecone-client package required: pip install pinecone-client")

    @property
    def index(self):
        if self._index is None:
            self._init_client()
        return self._index

    def add(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None) -> list[str]:
        """Add documents (requires external embedding)."""
        # Note: Pinecone requires pre-computed embeddings
        raise NotImplementedError("Pinecone requires embeddings. Use add_embeddings instead.")

    def add_embeddings(self, embeddings: list[list[float]], metadatas: list[dict], ids: list[str]) -> list[str]:
        """Add pre-computed embeddings."""
        vectors = [
            {"id": id, "values": emb, "metadata": meta}
            for id, emb, meta in zip(ids, embeddings, metadatas)
        ]
        self.index.upsert(vectors=vectors)
        return ids

    def search(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        """Search (requires query embedding)."""
        raise NotImplementedError("Pinecone requires query embedding. Use search_by_vector instead.")

    def search_by_vector(self, query_vector: list[float], top_k: int = 5, filters: dict = None) -> list[dict]:
        """Search by vector."""
        results = self.index.query(vector=query_vector, top_k=top_k, filter=filters, include_metadata=True)
        return [
            {"id": m.id, "score": m.score, "metadata": m.metadata}
            for m in results.matches
        ]

    def delete(self, ids: list[str]) -> bool:
        """Delete vectors."""
        self.index.delete(ids=ids)
        return True


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for development."""

    def __init__(self):
        self.documents: dict[str, dict] = {}
        self._id_counter = 0

    def _simple_embedding(self, text: str) -> list[float]:
        """Simple embedding for demo."""
        vector = [0.0] * 384
        for i, char in enumerate(text.lower()[:384]):
            vector[i] = ord(char) / 255.0
        magnitude = math.sqrt(sum(v * v for v in vector))
        return [v / magnitude for v in vector] if magnitude > 0 else vector

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(a * b for a, b in zip(v1, v2))
        m1 = math.sqrt(sum(a * a for a in v1))
        m2 = math.sqrt(sum(b * b for b in v2))
        return dot / (m1 * m2) if m1 and m2 else 0.0

    def add(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None) -> list[str]:
        """Add documents."""
        result_ids = []
        for i, text in enumerate(texts):
            doc_id = ids[i] if ids else f"doc_{self._id_counter}"
            self._id_counter += 1
            self.documents[doc_id] = {
                "id": doc_id,
                "text": text,
                "embedding": self._simple_embedding(text),
                "metadata": metadatas[i] if metadatas else {}
            }
            result_ids.append(doc_id)
        return result_ids

    def search(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        """Search documents."""
        query_emb = self._simple_embedding(query)
        results = []
        for doc in self.documents.values():
            if filters:
                if not all(doc["metadata"].get(k) == v for k, v in filters.items()):
                    continue
            similarity = self._cosine_similarity(query_emb, doc["embedding"])
            results.append({"id": doc["id"], "text": doc["text"], "metadata": doc["metadata"], "similarity": similarity})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete(self, ids: list[str]) -> bool:
        """Delete documents."""
        for doc_id in ids:
            self.documents.pop(doc_id, None)
        return True


def get_vector_store(store_type: str = "memory") -> VectorStore:
    """Factory to get vector store by type."""
    if store_type == "chroma":
        return ChromaDBStore()
    elif store_type == "pinecone":
        return PineconeStore(index_name=getattr(settings, 'pinecone_index', 'default'))
    return InMemoryVectorStore()
