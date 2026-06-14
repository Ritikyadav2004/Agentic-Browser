"""
Shared Playwright browser management with anti-blocking strategies:
- Realistic user-agent rotation
- Randomized viewport
- Stealth-style JS overrides
- Random delays between actions
"""
from __future__ import annotations

import asyncio
import logging
import random
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, Route, async_playwright

from config import get_settings

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]


def get_user_agent() -> str:
    return random.choice(_USER_AGENTS)

_VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1920, "height": 1080},
]

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
"""


class BrowserManager:
    """Manages a single shared Playwright browser instance for the app lifecycle."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._browser is None:
                settings = get_settings()
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=settings.scraper_headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ],
                )
                logger.info("Playwright browser launched.")

    async def stop(self) -> None:
        async with self._lock:
            if self._browser is not None:
                await self._browser.close()
                self._browser = None
            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Playwright browser stopped.")

    @asynccontextmanager
    async def new_context(self):
        """Yield a fresh isolated browser context with anti-detection settings."""
        if self._browser is None:
            await self.start()
        assert self._browser is not None

        viewport = random.choice(_VIEWPORTS)
        user_agent = get_user_agent()

        context: BrowserContext = await self._browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 28.6139, "longitude": 77.2090},
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
            },
        )
        await context.add_init_script(_STEALTH_JS)

        try:
            yield context
        finally:
            await context.close()

    @asynccontextmanager
    async def new_page(self):
        """Yield a new page within a fresh context. Closes context on exit."""
        async with self.new_context() as context:
            page: Page = await context.new_page()
            
            # Block images, fonts, and media to speed up scraping
            async def block_media(route: Route):
                if route.request.resource_type in ["image", "media", "font"]:
                    await route.abort()
                else:
                    await route.continue_()
            
            await page.route("**/*", block_media)
            
            settings = get_settings()
            page.set_default_timeout(settings.scraper_timeout_ms)
            try:
                yield page
            finally:
                await page.close()


async def random_delay(min_ms: int = 300, max_ms: int = 1200) -> None:
    """Sleep for a random short duration to mimic human browsing patterns."""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


browser_manager = BrowserManager()
