"""
Croma product search scraper.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

from playwright.async_api import Page

from models.schemas import ProductSpec
from services.browser_manager import random_delay
from tools.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CromaScraper(BaseScraper):
    SOURCE_NAME = "Croma"
    BASE_URL = "https://www.croma.com/searchB?q="

    def build_search_url(self, keywords: str) -> str:
        return f"{self.BASE_URL}{quote_plus(keywords)}%3Arelevance&text={quote_plus(keywords)}"

    async def scrape_listing(self, page: Page, max_results: int) -> list[ProductSpec]:
        products: list[ProductSpec] = []

        try:
            await page.wait_for_selector("li.product-item, div.product-item", timeout=15000)
        except Exception:
            logger.warning("[Croma] No product items found")
            return products

        cards = await page.query_selector_all("li.product-item, div.product-item")

        for card in cards[: max_results * 2]:
            if len(products) >= max_results:
                break
            try:
                title_el = await card.query_selector("h3.product-title, a.product-title, h3")
                title = (await title_el.inner_text()).strip() if title_el else None
                if not title:
                    continue

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else None
                url = (
                    f"https://www.croma.com{href}"
                    if href and href.startswith("/")
                    else href
                )

                price_el = await card.query_selector("span.amount, span.new-price, span.price")
                price = self.parse_price(await price_el.inner_text()) if price_el else None

                rating_el = await card.query_selector("span.rating-text, div.rating-section span")
                rating = self.parse_rating(await rating_el.inner_text()) if rating_el else None

                reviews_el = await card.query_selector("span.rating-count, a.review-link")
                reviews_count = self.parse_reviews_count(await reviews_el.inner_text()) if reviews_el else None

                image_el = await card.query_selector("img")
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
                logger.exception("[Croma] Failed to parse a product card")
                continue

        return products
