"""
Routes for product search and comparison.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from agents.ranking_agent import ranking_agent
from agents.workflow import run_shopping_workflow
from models.schemas import (
    CompareProductsRequest,
    CompareProductsResponse,
    ParsedQuery,
    SearchProductsRequest,
    SearchProductsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["products"])


@router.post("/search-products", response_model=SearchProductsResponse)
async def search_products(request: SearchProductsRequest) -> SearchProductsResponse:
    """
    Run the full LangGraph shopping agent workflow for a natural language query:
    parse intent -> scrape sites -> normalize -> compare -> rank -> save memory.
    """
    try:
        final_state = await run_shopping_workflow(
            query=request.query,
            user_id=request.user_id or "anonymous",
            max_results_per_site=request.max_results_per_site,
        )
    except Exception:
        logger.exception("Shopping workflow failed")
        raise HTTPException(status_code=500, detail="Failed to process shopping query")

    return SearchProductsResponse(
        parsed_query=final_state["parsed_query"],
        products=final_state.get("products", []),
        recommendation=final_state["recommendation"],
        session_id=final_state["session_id"],
    )


@router.post("/compare-products", response_model=CompareProductsResponse)
async def compare_products(request: CompareProductsRequest) -> CompareProductsResponse:
    """
    Compare and rank a user-supplied list of products (e.g. selected from previous
    search results) using the Claude-based ranking agent.
    """
    if not request.products:
        raise HTTPException(status_code=400, detail="At least one product is required")

    parsed_query = ParsedQuery(
        category="other",
        budget=request.budget,
        min_budget=None,
        purpose=request.purpose,
        preferences=[],
        raw_query="manual comparison",
        search_keywords="",
        sites=[],
    )

    try:
        recommendation = await ranking_agent.rank(request.products, parsed_query)
    except Exception:
        logger.exception("Comparison ranking failed")
        raise HTTPException(status_code=500, detail="Failed to compare products")

    return CompareProductsResponse(recommendation=recommendation)
