"""
Vector memory manager backed by ChromaDB.

Stores embeddings of past user queries + recommendations so the agent can
recall similar past searches and provide context-aware suggestions.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB is not installed or failed to import. Search memory features will be disabled.")

from config import get_settings

_chroma_client: Optional[Any] = None
_collection = None

_COLLECTION_NAME = "shopping_memory"


def _get_client() -> Any:
    global _chroma_client
    if not CHROMA_AVAILABLE:
        raise RuntimeError("ChromaDB is not installed.")
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def _get_collection():
    global _collection
    if not CHROMA_AVAILABLE:
        raise RuntimeError("ChromaDB is not installed.")
    if _collection is None:
        client = _get_client()
        # Default embedding function (all-MiniLM-L6-v2) runs locally, no API key needed.
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        _collection = client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


class MemoryManager:
    """Handles persistence and retrieval of search memory in ChromaDB."""

    @staticmethod
    def save_search_memory(
        user_id: str,
        session_id: str,
        query: str,
        parsed_query: dict[str, Any],
        recommendation_summary: str,
    ) -> None:
        """Persist a search session as a vector memory entry."""
        try:
            collection = _get_collection()
            doc_text = (
                f"Query: {query}\n"
                f"Category: {parsed_query.get('category')}\n"
                f"Budget: {parsed_query.get('budget')}\n"
                f"Purpose: {parsed_query.get('purpose')}\n"
                f"Recommendation: {recommendation_summary}"
            )
            collection.add(
                ids=[str(uuid.uuid4())],
                documents=[doc_text],
                metadatas=[
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "category": str(parsed_query.get("category", "")),
                        "budget": float(parsed_query.get("budget") or 0),
                        "purpose": str(parsed_query.get("purpose", "")),
                        "query": query,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                ],
            )
        except Exception:
            logger.exception("Failed to save search memory to ChromaDB")

    @staticmethod
    def recall_similar_searches(query: str, user_id: Optional[str] = None, n_results: int = 3) -> list[dict[str, Any]]:
        """Retrieve semantically similar past searches."""
        try:
            collection = _get_collection()
            where_filter = {"user_id": user_id} if user_id else None
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )
            output: list[dict[str, Any]] = []
            documents = results.get("documents") or [[]]
            metadatas = results.get("metadatas") or [[]]
            for doc, meta in zip(documents[0], metadatas[0]):
                output.append({"document": doc, "metadata": meta})
            return output
        except Exception:
            logger.exception("Failed to recall similar searches from ChromaDB")
            return []


memory_manager = MemoryManager()
