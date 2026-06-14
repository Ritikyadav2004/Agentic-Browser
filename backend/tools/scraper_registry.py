"""
Central registry mapping site keys to scraper instances, and category -> sites mapping.
"""
from __future__ import annotations

from tools.amazon_scraper import AmazonScraper
from tools.croma_scraper import CromaScraper
from tools.flipkart_scraper import FlipkartScraper
from tools.ikea_scraper import IkeaScraper
from tools.reliance_digital_scraper import RelianceDigitalScraper

SCRAPER_REGISTRY = {
    "amazon": AmazonScraper(),
    "flipkart": FlipkartScraper(),
    "croma": CromaScraper(),
    "reliance_digital": RelianceDigitalScraper(),
    "ikea": IkeaScraper(),
}

# Default site sets per category. Used by the planner agent when the LLM
# doesn't explicitly choose sites.
CATEGORY_SITE_MAP: dict[str, list[str]] = {
    "laptop": ["amazon", "flipkart", "croma", "reliance_digital"],
    "phone": ["amazon", "flipkart", "croma", "reliance_digital"],
    "tablet": ["amazon", "flipkart", "croma", "reliance_digital"],
    "earbuds": ["amazon", "flipkart", "croma", "reliance_digital"],
    "headphones": ["amazon", "flipkart", "croma", "reliance_digital"],
    "monitor": ["amazon", "flipkart", "croma", "reliance_digital"],
    "smartwatch": ["amazon", "flipkart", "croma", "reliance_digital"],
    "camera": ["amazon", "flipkart", "croma", "reliance_digital"],
    "furniture": ["ikea", "amazon", "flipkart"],
    "other": ["amazon", "flipkart"],
}


def get_sites_for_category(category: str) -> list[str]:
    return CATEGORY_SITE_MAP.get(category.lower(), CATEGORY_SITE_MAP["other"])
