"""
LangGraph workflow orchestrating the full shopping agent pipeline:

START -> parse_query -> extract_budget_category -> search_websites -> scrape_products
-> normalize_data -> compare_products -> rank_products -> generate_recommendation
-> save_memory -> END

Note: in this implementation several conceptual steps (search_websites + scrape_products,
and compare_products + rank_products) are combined into single nodes because the
underlying agents already perform them together. The graph still models the full
conceptual pipeline as distinct nodes for clarity and extensibility.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.planner_agent import planner_agent
from agents.ranking_agent import ranking_agent
from agents.shopping_agent import shopping_agent
from database.mongodb import get_db
from database.redis_client import build_search_cache_key, cache_get, cache_set
from memory.memory_manager import memory_manager
from models.schemas import ParsedQuery, ProductSpec, RecommendationResult

logger = logging.getLogger(__name__)


class ShoppingState(TypedDict, total=False):
    """State object passed between LangGraph nodes."""

    raw_query: str
    user_id: str
    max_results_per_site: int | None
    session_id: str

    parsed_query: ParsedQuery
    products: list[ProductSpec]
    recommendation: RecommendationResult


# ---- Node implementations ----

async def node_parse_query(state: ShoppingState) -> ShoppingState:
    """Parse Query + Extract Budget & Category (planner agent)."""
    query = state["raw_query"]
    parsed = await planner_agent.parse(query)
    logger.info("Parsed query: %s", parsed.model_dump())
    return {"parsed_query": parsed}


async def node_search_and_scrape(state: ShoppingState) -> ShoppingState:
    """Search Websites + Scrape Products (shopping agent), with Redis caching."""
    parsed_query: ParsedQuery = state["parsed_query"]
    max_results = state.get("max_results_per_site")

    cache_key = build_search_cache_key(parsed_query.category, parsed_query.budget, parsed_query.purpose)
    cached = await cache_get(cache_key)
    if cached:
        logger.info("Cache hit for key=%s", cache_key)
        products = [ProductSpec(**item) for item in cached]
        return {"products": products}

    products = await shopping_agent.search_products(parsed_query, max_results_per_site=max_results)

    # Cache normalized results (as plain dicts) for reuse
    await cache_set(cache_key, [p.model_dump(mode="json") for p in products])

    return {"products": products}


async def node_normalize_data(state: ShoppingState) -> ShoppingState:
    """Normalize Data: persist raw scraped products to MongoDB for record-keeping."""
    products: list[ProductSpec] = state.get("products", [])
    if products:
        try:
            db = get_db()
            docs = [p.model_dump(mode="json") for p in products]
            for doc in docs:
                doc["session_id"] = state["session_id"]
            await db.products.insert_many(docs)
        except Exception:
            logger.exception("Failed to persist scraped products to MongoDB")
    return {"session_id": state["session_id"]}


async def node_compare_and_rank(state: ShoppingState) -> ShoppingState:
    """Compare Products + Rank Products (Claude-based ranking agent)."""
    products: list[ProductSpec] = state.get("products", [])
    parsed_query: ParsedQuery = state["parsed_query"]
    recommendation = await ranking_agent.rank(products, parsed_query)
    return {"recommendation": recommendation}


async def node_generate_recommendation(state: ShoppingState) -> ShoppingState:
    """Generate Final Recommendation: persist recommendation to MongoDB."""
    recommendation: RecommendationResult = state["recommendation"]
    try:
        db = get_db()
        await db.recommendations.insert_one(
            {
                "session_id": state["session_id"],
                "user_id": state["user_id"],
                "query": state["raw_query"],
                "parsed_query": state["parsed_query"].model_dump(mode="json"),
                "recommendation": recommendation.model_dump(mode="json"),
                "created_at": datetime.utcnow(),
            }
        )
    except Exception:
        logger.exception("Failed to persist recommendation to MongoDB")
    return {"session_id": state["session_id"]}


async def node_save_memory(state: ShoppingState) -> ShoppingState:
    """Save Memory: store search session in ChromaDB vector memory and Mongo history."""
    parsed_query: ParsedQuery = state["parsed_query"]
    recommendation: RecommendationResult = state["recommendation"]

    try:
        db = get_db()
        await db.search_history.insert_one(
            {
                "session_id": state["session_id"],
                "user_id": state["user_id"],
                "query": state["raw_query"],
                "parsed_query": parsed_query.model_dump(mode="json"),
            }
        )
    except Exception:
        logger.exception("Failed to persist search history to MongoDB")

    try:
        memory_manager.save_search_memory(
            user_id=state["user_id"],
            session_id=state["session_id"],
            query=state["raw_query"],
            parsed_query=parsed_query.model_dump(mode="json"),
            recommendation_summary=recommendation.why_recommended,
        )
    except Exception:
        logger.exception("Failed to save search memory to ChromaDB")

    return {"session_id": state["session_id"]}


def build_shopping_graph():
    """Construct and compile the LangGraph state machine."""
    graph = StateGraph(ShoppingState)

    graph.add_node("parse_query", node_parse_query)
    graph.add_node("search_and_scrape", node_search_and_scrape)
    graph.add_node("normalize_data", node_normalize_data)
    graph.add_node("compare_and_rank", node_compare_and_rank)
    graph.add_node("generate_recommendation", node_generate_recommendation)
    graph.add_node("save_memory", node_save_memory)

    graph.set_entry_point("parse_query")
    graph.add_edge("parse_query", "search_and_scrape")
    graph.add_edge("search_and_scrape", "normalize_data")
    graph.add_edge("normalize_data", "compare_and_rank")
    graph.add_edge("compare_and_rank", "generate_recommendation")
    graph.add_edge("generate_recommendation", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


_compiled_graph = None


def get_shopping_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_shopping_graph()
    return _compiled_graph


async def run_shopping_workflow(
    query: str,
    user_id: str = "anonymous",
    max_results_per_site: int | None = None,
) -> ShoppingState:
    """Convenience entrypoint: run the full LangGraph workflow for a user query."""
    graph = get_shopping_graph()
    initial_state: ShoppingState = {
        "raw_query": query,
        "user_id": user_id,
        "max_results_per_site": max_results_per_site,
        "session_id": str(uuid.uuid4()),
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state
