"""
Ranking Agent: uses Claude to compare and rank scraped products across
price, performance, ratings, durability, value for money, and use-case fit.
"""
from __future__ import annotations

import logging

from models.schemas import ParsedQuery, ProductSpec, RecommendationResult
from services.claude_service import call_claude, extract_json

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are an expert shopping advisor for Indian consumers, specializing in
electronics and furniture. You will be given a list of scraped products (each having a "product_id" starting from 0) plus the user's intent (category, budget, purpose, preferences).

Your task:
1. Evaluate each product on these factors (score each 0-10):
   - performance_score: how well it performs for the stated purpose
   - durability_score: expected build quality/longevity based on brand/specs/reviews
   - value_for_money_score: price relative to features and quality
   - use_case_fit_score: how well it matches the user's stated purpose/preferences
2. Compute an overall_score (0-10) as a weighted combination you deem appropriate.
3. Select:
   - best_choice: the single best overall product (best balance of all factors)
   - budget_choice: the cheapest product that is still reasonably good (rating >= 3.5 if possible)
   - premium_choice: the highest-quality/most premium product within or slightly above budget
4. Build a comparison_table: an array containing one entry for every product in the list.

Respond ONLY with a valid JSON object (no extra prose, no markdown code blocks) with this exact shape:
{
  "best_choice": { "product_id": <int>, "reason": "<short 1-2 sentence explanation>" },
  "budget_choice": { "product_id": <int>, "reason": "<short 1-2 sentence explanation>" },
  "premium_choice": { "product_id": <int>, "reason": "<short 1-2 sentence explanation>" },
  "comparison_table": [
    {
      "product_id": <int>,
      "performance_score": <number 0-10>,
      "durability_score": <number 0-10>,
      "value_for_money_score": <number 0-10>,
      "use_case_fit_score": <number 0-10>,
      "overall_score": <number 0-10>
    }
  ],
  "why_recommended": "<concise 2-3 sentence overall summary>"
}

Rules:
- In best_choice, budget_choice, premium_choice, and comparison_table, DO NOT include fields like title, price, url, source, rating, or reviews_count. Only use "product_id" (the integer index of the product in the input list).
- If the product list is empty, return empty objects/arrays and explain in why_recommended that no products were found."""


class RankingAgent:
    """Compares and ranks products using Claude, returning a structured recommendation."""

    async def rank(self, products: list[ProductSpec], parsed_query: ParsedQuery) -> RecommendationResult:
        if not products:
            return RecommendationResult(
                best_choice={},
                budget_choice={},
                premium_choice={},
                comparison_table=[],
                why_recommended=(
                    "No products were found matching your criteria. "
                    "Try increasing your budget or adjusting your search terms."
                ),
            )

        product_payload = [
            {
                "product_id": i,
                "title": p.title,
                "source": p.source,
                "price": p.price,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "availability": p.availability,
                "specifications": p.specifications,
            }
            for i, p in enumerate(products)
        ]

        user_prompt = (
            f"User intent:\n"
            f"- category: {parsed_query.category}\n"
            f"- budget: {parsed_query.budget}\n"
            f"- purpose: {parsed_query.purpose}\n"
            f"- preferences: {parsed_query.preferences}\n\n"
            f"Products (JSON array):\n{product_payload}"
        )

        try:
            raw_response = await call_claude(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=4000,
                temperature=0.2,
            )
            data = extract_json(raw_response)
        except Exception:
            logger.exception("Ranking agent failed, falling back to heuristic ranking")
            return self._fallback_rank(products, parsed_query)

        try:
            def reconstruct_item(item: dict) -> dict:
                if not item:
                    return {}
                pid = item.get("product_id")
                if pid is not None:
                    try:
                        idx = int(float(pid))
                        if 0 <= idx < len(products):
                            p = products[idx]
                            return {
                                "title": p.title,
                                "source": p.source,
                                "price": p.price,
                                "rating": p.rating,
                                "reviews_count": p.reviews_count,
                                "performance_score": item.get("performance_score"),
                                "durability_score": item.get("durability_score"),
                                "value_for_money_score": item.get("value_for_money_score"),
                                "use_case_fit_score": item.get("use_case_fit_score"),
                                "overall_score": item.get("overall_score"),
                                "url": p.url,
                                "reason": item.get("reason"),
                            }
                    except (ValueError, TypeError):
                        pass
                return {}

            best_choice = reconstruct_item(data.get("best_choice") or {})
            budget_choice = reconstruct_item(data.get("budget_choice") or {})
            premium_choice = reconstruct_item(data.get("premium_choice") or {})
            
            raw_table = data.get("comparison_table") or []
            comparison_table = []
            for entry in raw_table:
                reconstructed = reconstruct_item(entry)
                if reconstructed:
                    reconstructed.pop("reason", None)  # Clean up reason in table rows
                    comparison_table.append(reconstructed)

            return RecommendationResult(
                best_choice=best_choice,
                budget_choice=budget_choice,
                premium_choice=premium_choice,
                comparison_table=comparison_table,
                why_recommended=data.get("why_recommended") or "",
            )
        except Exception:
            logger.exception("Failed to coerce Claude ranking output, using fallback")
            return self._fallback_rank(products, parsed_query)

    @staticmethod
    def _fallback_rank(products: list[ProductSpec], parsed_query: ParsedQuery) -> RecommendationResult:
        """Simple heuristic ranking if Claude is unavailable."""
        scored = []
        for p in products:
            price = p.price or 0
            rating = p.rating or 3.0
            value_score = (rating / max(price, 1)) * 10000
            scored.append((p, rating, value_score))

        # Best choice: highest rating, then best value
        best = max(scored, key=lambda t: (t[1], t[2]))[0]
        # Budget choice: cheapest with rating >= 3.5, else cheapest overall
        decent = [p for p in products if (p.rating or 0) >= 3.5]
        budget = min(decent or products, key=lambda p: p.price or float("inf"))
        # Premium choice: most expensive
        premium = max(products, key=lambda p: p.price or 0)

        def to_entry(p: ProductSpec, reason: str) -> dict:
            return {
                "title": p.title,
                "source": p.source,
                "price": p.price,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "performance_score": None,
                "durability_score": None,
                "value_for_money_score": None,
                "use_case_fit_score": None,
                "overall_score": p.rating,
                "url": p.url,
                "reason": reason,
            }

        comparison_table = [
            {
                "title": p.title,
                "source": p.source,
                "price": p.price,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "performance_score": None,
                "durability_score": None,
                "value_for_money_score": None,
                "use_case_fit_score": None,
                "overall_score": p.rating,
                "url": p.url,
            }
            for p in products
        ]

        return RecommendationResult(
            best_choice=to_entry(best, "Highest rated option that fits your criteria."),
            budget_choice=to_entry(budget, "Most affordable option with acceptable ratings."),
            premium_choice=to_entry(premium, "Highest-priced option, likely with premium features."),
            comparison_table=comparison_table,
            why_recommended=(
                f"Based on available data, '{best.title}' from {best.source} offers the best "
                f"balance of price and rating for your {parsed_query.purpose or 'stated'} use case."
            ),
        )


ranking_agent = RankingAgent()
