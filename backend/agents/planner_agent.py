"""
Planner Agent: parses the user's natural language shopping query into a
structured representation (category, budget, purpose, preferences) using Claude.
"""
from __future__ import annotations

import logging

from models.schemas import ParsedQuery
from services.claude_service import call_claude, extract_json
from tools.scraper_registry import get_sites_for_category

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are a shopping intent parser for an Indian e-commerce assistant.
Given a user's natural language product query, extract structured information.

Respond ONLY with a valid JSON object (no markdown fences, no extra text) with this exact shape:
{
  "category": "<one of: laptop, phone, tablet, earbuds, headphones, monitor, smartwatch, camera, furniture, other>",
  "budget": <number or null, maximum budget in INR. Convert 'k'/'lakh' notations e.g. 50k -> 50000, 1 lakh -> 100000>,
  "min_budget": <number or null, minimum budget in INR if a range is given>,
  "purpose": "<short use case string, e.g. 'coding', 'gaming', 'gym', 'hostel room', or null>",
  "preferences": [<list of extra feature/preference strings the user mentioned, e.g. "lightweight", "long battery life">],
  "search_keywords": "<concise, e-commerce-friendly search string for this product, in English, without budget numbers>"
}

Rules:
- category must be the closest match from the allowed list. Use "furniture" for hostel room items, "other" if nothing fits.
- budget should be a plain number (no currency symbols, no commas).
- search_keywords should be 2-6 words suitable for typing into a search bar (e.g. "gaming laptop", "wireless earbuds for gym", "study table for hostel").
- If no budget is mentioned, set budget to null.
- Always return valid, parseable JSON."""


class PlannerAgent:
    """Extracts structured shopping intent from a raw user query."""

    async def parse(self, query: str) -> ParsedQuery:
        try:
            raw_response = await call_claude(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=query,
                max_tokens=500,
                temperature=0.0,
            )
            data = extract_json(raw_response)
        except Exception:
            logger.exception("Planner agent failed to parse query via Claude, using fallback heuristic")
            data = self._fallback_parse(query)

        category = str(data.get("category") or "other").lower()
        budget = data.get("budget")
        min_budget = data.get("min_budget")
        purpose = data.get("purpose")
        preferences = data.get("preferences") or []
        search_keywords = data.get("search_keywords") or query

        try:
            budget = float(budget) if budget is not None else None
        except (TypeError, ValueError):
            budget = None
        try:
            min_budget = float(min_budget) if min_budget is not None else None
        except (TypeError, ValueError):
            min_budget = None

        sites = get_sites_for_category(category)

        return ParsedQuery(
            category=category,
            budget=budget,
            min_budget=min_budget,
            purpose=purpose,
            preferences=preferences if isinstance(preferences, list) else [],
            raw_query=query,
            search_keywords=str(search_keywords),
            sites=sites,
        )

    @staticmethod
    def _fallback_parse(query: str) -> dict:
        """Very simple keyword-based fallback if Claude call fails entirely."""
        q = query.lower()
        category = "other"
        category_keywords = {
            "laptop": ["laptop", "notebook"],
            "phone": ["phone", "smartphone", "mobile"],
            "tablet": ["tablet", "ipad"],
            "earbuds": ["earbud", "earphone", "tws"],
            "headphones": ["headphone", "headset"],
            "monitor": ["monitor", "display"],
            "smartwatch": ["smartwatch", "watch"],
            "camera": ["camera", "dslr"],
            "furniture": ["furniture", "table", "chair", "bed", "desk", "wardrobe", "shelf", "hostel"],
        }
        for cat, kws in category_keywords.items():
            if any(kw in q for kw in kws):
                category = cat
                break

        import re

        budget = None
        # Try matching numbers associated with budget context or currency markers first
        match = re.search(r"(?:under|below|budget|max|maximum|around|approx|₹|rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh|l)?\b", q)
        if not match:
            # Try matching a number followed by a unit (e.g. 50k, 50k)
            match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh|l)\b", q)
        if not match:
            # Try matching any number, but ignore if followed by common hardware capacity specs (gb, tb, hz, etc.)
            match = re.search(r"\b(\d+(?:,\d+)*(?:\.\d+)?)\s*(?!(?:gb|tb|hz|ghz|mah|core|mp)\b)(k|thousand|lakh|l)?\b", q)

        if match:
            value = float(match.group(1).replace(",", ""))
            unit = match.group(2)
            if unit in ("k", "thousand"):
                value *= 1000
            elif unit in ("lakh", "l"):
                value *= 100000
            budget = value

        return {
            "category": category,
            "budget": budget,
            "min_budget": None,
            "purpose": None,
            "preferences": [],
            "search_keywords": query,
        }


planner_agent = PlannerAgent()
