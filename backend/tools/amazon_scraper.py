"""
Amazon India product search scraper.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

from playwright.async_api import Page

from models.schemas import ProductSpec
from services.browser_manager import random_delay
from tools.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    SOURCE_NAME = "Amazon"
    BASE_URL = "https://www.amazon.in/s?k="

    def build_search_url(self, keywords: str) -> str:
        return f"{self.BASE_URL}{quote_plus(keywords)}"

    async def scrape_listing(self, page: Page, max_results: int) -> list[ProductSpec]:
        products: list[ProductSpec] = []

        try:
            await page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15000)
        except Exception:
            logger.warning("[Amazon] Search results container not found")
            return products

        cards = await page.query_selector_all('div[data-component-type="s-search-result"]')

        for card in cards[: max_results * 2]:  # iterate extra in case some are sponsored/empty
            if len(products) >= max_results:
                break
            try:
                title_el = await card.query_selector("h2 a span") or await card.query_selector("h2 span")
                title = (await title_el.inner_text()).strip() if title_el else None
                if not title:
                    continue

                link_el = await card.query_selector("h2 a")
                href = await link_el.get_attribute("href") if link_el else None
                url = f"https://www.amazon.in{href}" if href and href.startswith("/") else href

                price_whole = await card.query_selector("span.a-price-whole")
                price_text = await price_whole.inner_text() if price_whole else None
                price = self.parse_price(price_text)

                rating_el = await card.query_selector("span.a-icon-alt")
                rating_text = await rating_el.get_attribute("textContent") if rating_el else None
                if not rating_text and rating_el:
                    rating_text = await rating_el.inner_text()
                rating = self.parse_rating(rating_text)

                reviews_el = await card.query_selector("span.a-size-base.s-underline-text")
                if not reviews_el:
                    reviews_candidates = await card.query_selector_all("span.a-size-base")
                    reviews_el = reviews_candidates[-1] if reviews_candidates else None
                reviews_text = await reviews_el.inner_text() if reviews_el else None
                reviews_count = self.parse_reviews_count(reviews_text)

                image_el = await card.query_selector("img.s-image")
                image_url = await image_el.get_attribute("src") if image_el else None

                availability = "In Stock" if price is not None else "Check on site"

                products.append(
                    ProductSpec(
                        source=self.SOURCE_NAME,
                        title=title,
                        price=price,
                        rating=rating,
                        reviews_count=reviews_count,
                        availability=availability,
                        specifications={},
                        url=url,
                        image_url=image_url,
                    )
                )
                await random_delay(100, 300)
            except Exception:
                logger.exception("[Amazon] Failed to parse a product card")
                continue

        return products
