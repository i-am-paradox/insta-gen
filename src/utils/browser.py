import logging
from playwright.async_api import async_playwright, BrowserContext, Browser
from playwright_stealth import stealth_async
from typing import Optional, Dict

logger = logging.getLogger(__name__)

async def create_stealth_context(browser: Browser, proxy: Optional[Dict[str, str]] = None) -> BrowserContext:
    """
    Creates a new browser context with stealth evasions applied.
    """
    context_args = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 720},
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    }

    if proxy:
        context_args["proxy"] = proxy

    context = await browser.new_context(**context_args)
    
    # Apply stealth evasions
    await stealth_async(context)
    
    return context

async def get_browser_instance(playwright, headless: bool = True) -> Browser:
    """Launches the Chromium browser instance."""
    return await playwright.chromium.launch(headless=headless)
