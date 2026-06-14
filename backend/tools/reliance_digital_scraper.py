"""
Reliance Digital product search scraper.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

from playwright.async_api import Page

from models.schemas import ProductSpec
from services.browser_manager import random_delay
from tools.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RelianceDigitalScraper(BaseScraper):
    SOURCE_NAME = "Reliance Digital"
    BASE_URL = "https://www.reliancedigital.in/search?q="

    def build_search_url(self, keywords: str) -> str:
        return f"{self.BASE_URL}{quote_plus(keywords)}:relevance&searchQuery={quote_plus(keywords)}"

    async def scrape_listing(self, page: Page, max_results: int) -> list[ProductSpec]:
        products: list[ProductSpec] = []

        try:
            await page.wait_for_selector("div.sp__product, div.pl__container li", timeout=15000)
        except Exception:
            logger.warning("[Reliance Digital] No product items found")
            return products

        cards = await page.query_selector_all("div.sp__product, div.pl__container li")

        for card in cards[: max_results * 2]:
            if len(products) >= max_results:
                break
            try:
                title_el = await card.query_selector("p.sp__name, p.pl__title, h3")
                title = (await title_el.inner_text()).strip() if title_el else None
                if not title:
                    continue

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else None
                url = (
                    f"https://www.reliancedigital.in{href}"
                    if href and href.startswith("/")
                    else href
                )

                price_el = await card.query_selector("span.product__price--discounted, span.sp__price, span.pl__price")
                price = self.parse_price(await price_el.inner_text()) if price_el else None

                rating_el = await card.query_selector("div.pl__rating, span.rating")
                rating = self.parse_rating(await rating_el.inner_text()) if rating_el else None

                reviews_count = None  # Reliance Digital rarely shows review counts in listing

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
                logger.exception("[Reliance Digital] Failed to parse a product card")
                continue

        return products
