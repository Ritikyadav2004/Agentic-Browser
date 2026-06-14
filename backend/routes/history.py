"""
Routes for search history and recommendations retrieval.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from database.mongodb import get_db
from models.schemas import RecommendationsResponse, SearchHistoryItem, SearchHistoryResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])


@router.get("/search-history", response_model=SearchHistoryResponse)
async def get_search_history(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=20, ge=1, le=100),
) -> SearchHistoryResponse:
    """Return the most recent search history entries for a given user."""
    db = get_db()
    cursor = db.search_history.find({"user_id": user_id}).sort("_id", -1).limit(limit)

    items: list[SearchHistoryItem] = []
    async for doc in cursor:
        items.append(
            SearchHistoryItem(
                session_id=doc.get("session_id", ""),
                user_id=doc.get("user_id", "anonymous"),
                query=doc.get("query", ""),
                parsed_query=doc.get("parsed_query", {}),
                created_at=doc.get("_id").generation_time if doc.get("_id") else doc.get("created_at"),
            )
        )

    return SearchHistoryResponse(items=items)


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=10, ge=1, le=50),
) -> RecommendationsResponse:
    """Return the most recent recommendation results for a given user."""
    db = get_db()
    cursor = db.recommendations.find({"user_id": user_id}).sort("_id", -1).limit(limit)

    items: list[dict] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)

    return RecommendationsResponse(items=items)
