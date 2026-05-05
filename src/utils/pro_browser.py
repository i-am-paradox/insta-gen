import logging
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, Page
from typing import Optional, Dict

logger = logging.getLogger("BrowserMgr")


class BrowserManager:
    """
    Manages a SINGLE Camoufox browser instance.
    Workers create new TABS (pages) within this one browser.
    This avoids launching multiple Firefox processes.
    """

    def __init__(self, headless: bool = False, humanize: bool = True,
                 proxy: Optional[Dict[str, str]] = None):
        self.headless = headless
        self.humanize = humanize
        self.proxy = proxy
        self._camoufox: Optional[AsyncCamoufox] = None
        self._browser: Optional[Browser] = None

    async def start(self):
        """Launch the single Camoufox browser instance."""
        logger.info(f"🚀 Launching Camoufox (headless={self.headless}, humanize={self.humanize})")

        # Mobile viewport — iPhone 14 Pro size, easy to record
        MOBILE_W, MOBILE_H = 390, 844

        browser_args = {
            "headless": self.headless,
            "humanize": self.humanize,
            "screen": {"width": MOBILE_W, "height": MOBILE_H},
        }
        if self.proxy:
            browser_args["proxy"] = self.proxy

        self._camoufox = AsyncCamoufox(**browser_args)
        self._browser = await self._camoufox.__aenter__()
        logger.info("✅ Browser launched successfully (mobile 390×844)")
        return self

    async def new_tab(self) -> Page:
        """Open a new tab (page) in the existing browser."""
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")

        page = await self._browser.new_page()
        # Force mobile viewport on every tab
        await page.set_viewport_size({"width": 390, "height": 844})
        logger.debug(f"📄 New tab opened 390×844 (total: {len(await self.get_all_tabs())})")
        return page

    async def get_all_tabs(self):
        """Get all open pages/tabs."""
        if not self._browser:
            return []
        # Browser object
        if hasattr(self._browser, 'contexts'):
            pages = []
            for ctx in self._browser.contexts:
                pages.extend(ctx.pages)
            return pages
        # BrowserContext object
        if hasattr(self._browser, 'pages'):
            return self._browser.pages
        return []

    async def close_tab(self, page: Page):
        """Close a specific tab."""
        try:
            if not page.is_closed():
                await page.close()
        except Exception:
            pass

    async def shutdown(self):
        """Close the browser and all tabs."""
        logger.info("🛑 Shutting down browser...")
        if self._camoufox:
            try:
                await self._camoufox.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Browser shutdown warning: {e}")
        self._browser = None
        self._camoufox = None
        logger.info("✅ Browser closed")

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *args):
        await self.shutdown()
