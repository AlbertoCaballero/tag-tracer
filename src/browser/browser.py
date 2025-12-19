"""Browser management module for TagTracer.
Responsible for initializing Playwright, launching a headless browser,
managing browser contexts, and exposing utilities for page navigation.

TODO:
- Implement async Playwright lifecycle management
- Add support for headful mode
- Add logging and debugging hooks
"""

from typing import List

from playwright.async_api import Page, Request, async_playwright

from src.models import NetworkRequest


class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.p = None
        self.browser = None
        self.page = None
        self.captured_requests: List[NetworkRequest] = []

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
        Launches a headless browser instance and returns a new page object.
        """
        self.p = await async_playwright().start()
        self.browser = await self.p.chromium.launch(
            headless=self.headless, args=["--disable-http2"]
        )
        self.page = await self.browser.new_page()
        self.page.on("request", self._handle_request)
        return self.page

    async def navigate(self, url: str):
        """
        Navigates the page to the specified URL.
        """
        if not self.page:
            raise ConnectionError("Browser not launched. Call launch() first.")
        print(f"[Browser] Navigating to: {url}")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("\n[Browser] Navigation complete.")

    def get_captured_requests(self) -> List[NetworkRequest]:
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
