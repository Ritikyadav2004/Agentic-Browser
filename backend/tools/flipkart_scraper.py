"""
Flipkart product search scraper.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

from playwright.async_api import Page

from models.schemas import ProductSpec
from services.browser_manager import random_delay
from tools.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    SOURCE_NAME = "Flipkart"
    BASE_URL = "https://www.flipkart.com/search?q="

    def build_search_url(self, keywords: str) -> str:
        return f"{self.BASE_URL}{quote_plus(keywords)}"

    async def scrape_listing(self, page: Page, max_results: int) -> list[ProductSpec]:
        products: list[ProductSpec] = []

        # Dismiss the login popup if present
        try:
            close_btn = await page.query_selector("button._2KpZ6l._2doB4z")
            if close_btn:
                await close_btn.click()
                await random_delay(200, 500)
        except Exception:
            pass

        # Flipkart markup varies between grid (electronics) and list (general) layouts.
        # Try common card selectors in order.
        card_selectors = [
            "div[data-id]",             # Extremely stable selector matching data-id attribute on search result items
            "div._1AtVbE div._13oc-S",  # grid layout wrapper
            "div._2kHMtA",  # list layout cards
            "div._4ddWXP",  # alternate card
            "div._1xHGtK",  # mobile-style card
            "div.slgYqO",
            "div.yKfJKb",
            "div.cPHK7B",
        ]

        cards = []
        for selector in card_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                cards = await page.query_selector_all(selector)
                if cards:
                    break
            except Exception:
                continue

        if not cards:
            logger.warning("[Flipkart] No product cards found with known selectors")
            return products

        for card in cards[: max_results * 2]:
            if len(products) >= max_results:
                break
            try:
                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else None
                url = f"https://www.flipkart.com{href}" if href and href.startswith("/") else href

                image_el = await card.query_selector("img")
                image_url = await image_el.get_attribute("src") if image_el else None

                title = None
                for title_selector in ("div._4rR01T", "a.s1Q9rs", "a.IRpwTa", "div.KzDlHZ", "a.wjcEIp", "div._2WkVRV", "a._2WkVRV"):
                    title_el = await card.query_selector(title_selector)
                    if title_el:
                        title = (await title_el.inner_text()).strip()
                        break
                
                # Robust Fallbacks for title
                if not title and link_el:
                    title = await link_el.get_attribute("title")
                if not title and image_el:
                    title = await image_el.get_attribute("alt")
                
                if title:
                    title = title.strip()
                else:
                    continue

                price = None
                for price_selector in ("div._30jeq3", "div.Nx9bqj", "div._1vC4OI", "span.L3n15G", "span.pcriDe"):
                    price_el = await card.query_selector(price_selector)
                    if price_el:
                        price = self.parse_price(await price_el.inner_text())
                        break
                
                if price is None:
                    # Fallback: look for any element containing the Rupee symbol inside this card
                    price_el = await card.query_selector("text=/₹/")
                    if price_el:
                        price = self.parse_price(await price_el.inner_text())

                rating = None
                for rating_selector in ("div._3LWZlK", "div.XQDdHH", "span.Y1tV", "div.hGSR34"):
                    rating_el = await card.query_selector(rating_selector)
                    if rating_el:
                        rating = self.parse_rating(await rating_el.inner_text())
                        break

                reviews_count = None
                for reviews_selector in ("span._2_R_DZ", "span.Wphh3N", "span.ij2Yeb"):
                    reviews_el = await card.query_selector(reviews_selector)
                    if reviews_el:
                        reviews_count = self.parse_reviews_count(await reviews_el.inner_text())
                        break

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
                logger.exception("[Flipkart] Failed to parse a product card")
                continue

        return products
