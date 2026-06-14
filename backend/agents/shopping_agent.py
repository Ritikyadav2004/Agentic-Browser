"""
Shopping Agent: orchestrates concurrent searches across multiple e-commerce
sites using the scraper registry, and normalizes/filters the results.
"""
from __future__ import annotations

import asyncio
import logging

from config import get_settings
from models.schemas import ParsedQuery, ProductSpec
from tools.scraper_registry import SCRAPER_REGISTRY

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """Coordinates scraping across all relevant sites for a parsed query."""

    async def search_products(self, parsed_query: ParsedQuery, max_results_per_site: int | None = None) -> list[ProductSpec]:
        settings = get_settings()
        max_results = max_results_per_site or settings.scraper_max_products_per_site

        sites = parsed_query.sites or list(SCRAPER_REGISTRY.keys())
        keywords = parsed_query.search_keywords

        tasks = []
        site_names = []
        for site_key in sites:
            scraper = SCRAPER_REGISTRY.get(site_key)
            if scraper is None:
                logger.warning("No scraper registered for site=%s, skipping", site_key)
                continue
            tasks.append(scraper.search(keywords, max_results=max_results))
            site_names.append(site_key)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_products: list[ProductSpec] = []
        for site_key, result in zip(site_names, results):
            if isinstance(result, Exception):
                logger.error("Scraper %s raised an exception: %s", site_key, result)
                continue
            all_products.extend(result)

        return self._normalize_and_filter(all_products, parsed_query)

    @staticmethod
    def _normalize_and_filter(products: list[ProductSpec], parsed_query: ParsedQuery) -> list[ProductSpec]:
        """Deduplicate, filter by budget, and clean up scraped products."""
        seen_titles: set[str] = set()
        normalized: list[ProductSpec] = []

        for product in products:
            if not product.title:
                continue

            title_key = product.title.strip().lower()[:80]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            # Filter out products with no price at all
            if product.price is None:
                continue

            # Apply budget filter with a small tolerance (10%) to avoid over-pruning
            if parsed_query.budget:
                upper_bound = parsed_query.budget * 1.10
                if product.price > upper_bound:
                    continue

            if parsed_query.min_budget and product.price < parsed_query.min_budget * 0.9:
                continue

            normalized.append(product)

        # Sort by rating desc (None last), then price asc
        normalized.sort(key=lambda p: (-(p.rating or 0), p.price or float("inf")))
        return normalized


shopping_agent = ShoppingAgent()
