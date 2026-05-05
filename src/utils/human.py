import asyncio
import random
import logging
from playwright.async_api import Page
from typing import Optional

logger = logging.getLogger("HumanEngine")


class HumanEngine:
    """
    Handles human-like interactions: typing, clicking, scrolling.
    Uses Playwright's keyboard API for natural typing (no char duplication).
    Mouse humanization is handled by Camoufox's built-in 'humanize' option.
    """

    @staticmethod
    async def move_and_click(page: Page, selector: str, timeout: int = 10000):
        """Click an element after waiting for it to be visible."""
        try:
            element = await page.wait_for_selector(selector, state="visible", timeout=timeout)
            if not element:
                logger.warning(f"Element not found: {selector}")
                return False

            # Small random delay before clicking (human hesitation)
            await asyncio.sleep(random.uniform(0.2, 0.6))
            await element.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            return True

        except Exception as e:
            logger.error(f"Failed click on {selector}: {e}")
            return False

    @staticmethod
    async def human_type(page: Page, selector: str, text: str, clear_first: bool = True):
        """
        Types text with randomized delays mimicking human cadence.
        Uses focus + keyboard.type to avoid the char-duplication bug.
        """
        try:
            element = await page.wait_for_selector(selector, state="visible", timeout=15000)
            if not element:
                logger.warning(f"Input not found: {selector}")
                return False

            await element.click()
            await asyncio.sleep(random.uniform(0.2, 0.5))

            # Clear existing content if needed
            if clear_first:
                await page.keyboard.press("Meta+a")  # Select all (Mac)
                await asyncio.sleep(0.1)
                await page.keyboard.press("Backspace")
                await asyncio.sleep(0.2)

            # Type each character with human-like delays
            for i, char in enumerate(text):
                await page.keyboard.type(char, delay=random.randint(40, 180))

                # Occasional "thinking" pause (10% chance)
                if random.random() < 0.08:
                    await asyncio.sleep(random.uniform(0.3, 0.8))

            await asyncio.sleep(random.uniform(0.1, 0.3))
            return True

        except Exception as e:
            logger.error(f"Failed typing in {selector}: {e}")
            return False

    @staticmethod
    async def random_scroll(page: Page, scrolls: int = 0):
        """Performs random jittery scrolls to simulate browsing."""
        count = scrolls if scrolls > 0 else random.randint(2, 4)
        for _ in range(count):
            scroll_amount = random.randint(100, 350)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.4, 1.0))

    @staticmethod
    async def random_mouse_movement(page: Page):
        """Move mouse to random positions to look alive."""
        for _ in range(random.randint(2, 4)):
            x = random.randint(100, 800)
            y = random.randint(100, 500)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.3, 0.8))

    @staticmethod
    async def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
        """Random delay to simulate human thinking time."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))
