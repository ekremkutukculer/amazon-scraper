"""BrowserManager — reusable stealth browser context manager for Amazon scraping."""

import logging
import random

from playwright.sync_api import sync_playwright

from config import DELAY_RANGE, PROXY, get_random_user_agent

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
]

BROWSER_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

WEBDRIVER_OVERRIDE = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    delete navigator.__proto__.webdriver;
"""


class BrowserManager:
    """Context manager that launches a stealth Playwright browser."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=STEALTH_ARGS,
        )

        context_kwargs = {
            "user_agent": get_random_user_agent(),
            "locale": "en-US",
            "viewport": {"width": 1920, "height": 1080},
            "extra_http_headers": BROWSER_HEADERS,
        }
        if PROXY:
            context_kwargs["proxy"] = {"server": PROXY}

        self._context = self._browser.new_context(**context_kwargs)

        # USD currency cookie
        self._context.add_cookies([{
            "name": "i18n-prefs",
            "value": "USD",
            "domain": ".amazon.com",
            "path": "/",
        }])

        self._page = self._context.new_page()
        self._page.add_init_script(WEBDRIVER_OVERRIDE)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        return False

    def get_page(self, url: str, wait_selector: str | None = None) -> str | None:
        """Navigate to *url*, retry up to MAX_RETRIES times.

        Returns the page HTML, or None if a CAPTCHA is detected or all
        attempts fail.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                self._page.wait_for_timeout(random.randint(2000, 4000))

                if wait_selector:
                    self._page.wait_for_selector(wait_selector, timeout=10000)

                html = self._page.content()

                # CAPTCHA detection
                if "validateCaptcha" in html:
                    logger.warning("CAPTCHA detected at %s", url)
                    return None

                return html

            except Exception as e:
                logger.warning(
                    "Attempt %d/%d for %s failed: %s", attempt, MAX_RETRIES, url, e
                )
                if attempt < MAX_RETRIES:
                    self._page.wait_for_timeout(random.randint(3000, 6000))

        logger.warning("All %d attempts failed for %s", MAX_RETRIES, url)
        return None

    def delay(self) -> None:
        """Random delay between requests using DELAY_RANGE from config."""
        wait_ms = int(random.uniform(*DELAY_RANGE) * 1000)
        self._page.wait_for_timeout(wait_ms)
