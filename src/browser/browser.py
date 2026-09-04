"""Browser management module for TagTracer.
Responsible for initializing Playwright, launching a headless browser,
managing browser contexts, and exposing utilities for page navigation.

TODO:
- Implement async Playwright lifecycle management
- Add support for headful mode
- Add logging and debugging hooks
"""

import asyncio

from playwright.async_api import Page, Request, async_playwright

from src.models import NetworkRequest


class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.p = None
        self.browser = None
        self.context = None
        self.page = None
        self.captured_requests: list[NetworkRequest] = []

    async def _handle_request(self, request: Request):
        self.captured_requests.append(
            NetworkRequest(
                url=request.url,
                method=request.method,
                headers=request.headers,
                post_data=request.post_data,
            )
        )

    async def launch(self) -> Page:
        """
        Launches a browser instance and returns a new page object.

        Headed mode is the default: it uses stealth configuration to reduce
        the chance of bot detection and blocking. Pass headless=True to run
        without a visible window.
        """
        self.p = await async_playwright().start()

        # Stealth configuration to reduce bot detection
        self.browser = await self.p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-http2",
                "--no-sandbox",
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
        )
        await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.page = await self.browser.new_page()
        self.page.on("request", self._handle_request)
        return self.page

    async def navigate(self, url: str, settle_time: float = 5.0):
        """
        Navigates the page to the specified URL and waits for the page to settle.

        Navigation completes at DOMContentLoaded, but analytics and marketing
        tags frequently fire on the `load` event or on a delay. We wait for the
        `load` event (best-effort) and then an extra `settle_time` seconds so
        late-firing tag beacons are captured.
        """
        if not self.page:
            raise ConnectionError("Browser not launched. Call launch() first.")
        print(f"\n[Browser] Navigating to: {url}")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            await self.page.wait_for_load_state("load", timeout=15000)
        except Exception:
            pass  # Page keeps loading past the load event; continue to settle
        if settle_time > 0:
            print(f"[Browser] Waiting {settle_time}s for tags to fire...")
            await asyncio.sleep(settle_time)
        print("\n[Browser] Navigation complete.")

    def get_captured_requests(self) -> list[NetworkRequest]:
        return self.captured_requests

    async def close(self):
        """
        Closes the browser and cleans up the Playwright instance.
        """
        if self.page:
            self.page.remove_listener("request", self._handle_request)
        if self.browser:
            await self.browser.close()
        if self.p:
            await self.p.stop()
