"""
LESSON 14: Vector Databases for AI/Embeddings
=============================================

Integrate vector databases for semantic search and AI.

Key Concepts:
- Vector embeddings
- Similarity search
- ChromaDB, pgvector, Pinecone
- RAG patterns

To run:
    uv run uvicorn lessons.03_advanced.04_vector_database:app --reload
"""

import math
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel


# =============================================================================
# Vector Database (Simulated)
# =============================================================================

class VectorDB:
    """
    Simulated vector database.

    In production, use:
    - ChromaDB: chromadb.Client()
    - Pinecone: pinecone.init(); pinecone.Index()
    - pgvector: PostgreSQL with vector extension
    """

    def __init__(self):
        self.documents: dict[str, dict] = {}
        self._id_counter = 0

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"doc_{self._id_counter}"

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def _simple_embedding(self, text: str) -> list[float]:
        """
        Simple text to vector (demo only).

        In production, use:
        - OpenAI: openai.Embedding.create(input=text, model="text-embedding-ada-002")
        - Sentence Transformers: model.encode(text)
        """
        # Simple character-based embedding (768 dims to match common models)
        vector = [0.0] * 768
        for i, char in enumerate(text.lower()[:768]):
            vector[i] = ord(char) / 255.0
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        return vector

    def add(self, text: str, metadata: dict = None) -> str:
        """Add document with embedding."""
        doc_id = self._next_id()
        embedding = self._simple_embedding(text)
        self.documents[doc_id] = {
            "id": doc_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        return doc_id

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for similar documents."""
        query_embedding = self._simple_embedding(query)

        results = []
        for doc in self.documents.values():
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "similarity": similarity
            })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete(self, doc_id: str) -> bool:
        """Delete document."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False


# Global instance
vector_db = VectorDB()


def get_vector_db() -> VectorDB:
    return vector_db


# =============================================================================
# Schemas
# =============================================================================

class DocumentCreate(BaseModel):
    text: str
    metadata: dict = {}


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    id: str
    text: str
    similarity: float
    metadata: dict


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize sample documents."""
    samples = [
        ("FastAPI is a modern Python web framework", {"category": "tech"}),
        ("Python is great for machine learning", {"category": "tech"}),
        ("Vectors enable semantic search", {"category": "ai"}),
        ("Embeddings capture meaning of text", {"category": "ai"}),
        ("PostgreSQL supports vector operations", {"category": "database"}),
        ("ChromaDB is an open-source vector database", {"category": "database"}),
    ]
    for text, meta in samples:
        vector_db.add(text, meta)
    print(f"Loaded {len(samples)} sample documents")
    yield


app = FastAPI(
    title="Vector Database Demo",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "database": "Vector DB (simulated)",
        "documents": len(vector_db.documents),
        "embedding_dim": 768
    }


@app.post("/documents")
async def add_document(doc: DocumentCreate, db: VectorDB = Depends(get_vector_db)):
    """Add document to vector database."""
    doc_id = db.add(doc.text, doc.metadata)
    return {"id": doc_id, "message": "Document added"}


@app.get("/documents")
async def list_documents(db: VectorDB = Depends(get_vector_db)):
    """List all documents."""
    return {
        "documents": [
            {"id": d["id"], "text": d["text"][:100], "metadata": d["metadata"]}
            for d in db.documents.values()
        ]
    }


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: VectorDB = Depends(get_vector_db)):
    """Delete document."""
    if not db.delete(doc_id):
        raise HTTPException(404, "Document not found")
    return {"message": "Document deleted"}


@app.post("/search", response_model=list[SearchResult])
async def search(query: SearchQuery, db: VectorDB = Depends(get_vector_db)):
    """Semantic search."""
    results = db.search(query.query, query.top_k)
    return results


@app.get("/search")
async def search_get(q: str, top_k: int = 5, db: VectorDB = Depends(get_vector_db)):
    """Semantic search (GET)."""
    return db.search(q, top_k)


# =============================================================================
# RAG Example
# =============================================================================

@app.post("/rag")
async def rag_example(query: str, db: VectorDB = Depends(get_vector_db)):
    """
    RAG (Retrieval-Augmented Generation) example.

    In production:
    1. Search for relevant documents
    2. Build prompt with context
    3. Send to LLM (OpenAI, Claude, etc.)
    """
    # 1. Retrieve relevant documents
    results = db.search(query, top_k=3)

    # 2. Build context
    context = "\n".join([f"- {r['text']}" for r in results])

    # 3. Build prompt (would send to LLM)
    prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""

    return {
        "query": query,
        "retrieved_docs": len(results),
        "context": context,
        "prompt": prompt,
        "note": "In production, send this prompt to an LLM"
    }


# =============================================================================
# Key Concepts
# =============================================================================

"""
VECTOR DATABASE CONCEPTS:
- Embeddings: Dense vector representations of text/data
- Similarity: Cosine, Euclidean, or dot product distance
- Index: Data structure for fast similarity search
- Metadata: Additional filterable fields

COMMON PROVIDERS:
- ChromaDB: Open-source, embedded or server
- Pinecone: Managed cloud service
- pgvector: PostgreSQL extension
- Weaviate: Open-source with GraphQL
- Qdrant: Open-source, Rust-based

EMBEDDING MODELS:
- OpenAI text-embedding-ada-002 (1536 dims)
- Sentence Transformers (384-768 dims)
- Cohere embed (1024-4096 dims)

RAG PATTERN:
1. User sends query
2. Convert query to embedding
3. Search vector DB for similar docs
4. Add docs as context to LLM prompt
5. LLM generates answer with context

USE CASES:
- Semantic search
- Recommendation systems
- Question answering
- Document similarity
- Image search (with CLIP)

CHROMADB EXAMPLE:
    import chromadb
    client = chromadb.Client()
    collection = client.create_collection("docs")
    collection.add(documents=["text"], ids=["id1"])
    results = collection.query(query_texts=["search"])
"""
