"""
Base scraper class providing shared retry logic, price/rating parsing helpers,
and a common interface for all site-specific scrapers.
"""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings
from models.schemas import ProductSpec
from services.browser_manager import browser_manager, random_delay

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for e-commerce scrapers."""

    SOURCE_NAME: str = "generic"

    def __init__(self) -> None:
        self.settings = get_settings()

    @abstractmethod
    def build_search_url(self, keywords: str) -> str:
        """Return the search results URL for the given keywords."""

    @abstractmethod
    async def scrape_listing(self, page: Page, max_results: int) -> list[ProductSpec]:
        """Scrape the search results page and return normalized ProductSpec list."""

    async def search(self, keywords: str, max_results: Optional[int] = None) -> list[ProductSpec]:
        """Public entrypoint: open a page, navigate, scrape, with retries."""
        max_results = max_results or self.settings.scraper_max_products_per_site
        try:
            return await self._search_with_retry(keywords, max_results)
        except Exception:
            logger.exception("Scraping failed for source=%s keywords=%s", self.SOURCE_NAME, keywords)
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        retry=retry_if_exception_type((PlaywrightTimeoutError, ConnectionError)),
        reraise=True,
    )
    async def _search_with_retry(self, keywords: str, max_results: int) -> list[ProductSpec]:
        url = self.build_search_url(keywords)
        async with browser_manager.new_page() as page:
            logger.info("[%s] Navigating to %s", self.SOURCE_NAME, url)
            await page.goto(url, wait_until="domcontentloaded")
            await random_delay(500, 1500)
            try:
                results = await self.scrape_listing(page, max_results)
            except PlaywrightTimeoutError:
                logger.warning("[%s] Timeout while scraping listing, returning partial/empty", self.SOURCE_NAME)
                results = []
            return results

    # ---- shared parsing helpers ----

    @staticmethod
    def parse_price(raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        cleaned = re.sub(r"[^\d.]", "", raw)
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def parse_rating(raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        match = re.search(r"(\d+(\.\d+)?)", raw)
        if not match:
            return None
        try:
            value = float(match.group(1))
            if 0 <= value <= 5:
                return value
            return None
        except ValueError:
            return None

    @staticmethod
    def parse_reviews_count(raw: Optional[str]) -> Optional[int]:
        if not raw:
            return None
        cleaned = re.sub(r"[^\d]", "", raw)
        if not cleaned:
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None
