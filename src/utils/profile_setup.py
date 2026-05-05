import random
import logging
import asyncio
from typing import Optional, Dict
from playwright.async_api import Page
from .human import HumanEngine

logger = logging.getLogger(__name__)

class ProfileBuilder:
    """Handles automatic profile customization to increase account trust."""
    
    def __init__(self):
        self.human = HumanEngine()

    async def setup_profile(self, page: Page, avatar_path: Optional[str] = None):
        """Uploads avatar and sets bio."""
        try:
            # Navigate to Edit Profile
            await page.goto("https://www.instagram.com/accounts/edit/", wait_until="networkidle")
            await asyncio.sleep(random.uniform(2, 4))
            
            # 1. Avatar Upload
            if avatar_path:
                logger.info(f"Uploading avatar from {avatar_path}...")
                async with page.expect_file_chooser() as fc_info:
                    await page.click("button:has-text('Change profile photo')")
                file_chooser = await fc_info.value
                await file_chooser.set_files(avatar_path)
                await asyncio.sleep(5)

            # 2. Bio Setup
            bios = [
                "Living life one day at a time ✨",
                "Photography | Travel | Tech 📸",
                "Dreamer. Believer. Achiever.",
                "Exploring the digital world 🌐",
                "Just here for the vibes ✌️"
            ]
            selected_bio = random.choice(bios)
            logger.info(f"Setting bio: {selected_bio}")
            await self.human.human_type(page, "textarea[id='pepBio']", selected_bio)
            
            await self.human.move_and_click(page, "button:has-text('Submit')")
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Profile setup failed: {e}")

    async def initial_activity(self, page: Page):
        """Follows 1-2 suggested accounts to build trust."""
        try:
            await page.goto("https://www.instagram.com/explore/people/", wait_until="networkidle")
            await asyncio.sleep(3)
            # Follow the first 2 'Follow' buttons
            follow_buttons = await page.query_selector_all("button:has-text('Follow')")
            for btn in follow_buttons[:2]:
                await btn.click()
                await asyncio.sleep(random.uniform(1, 3))
        except Exception as e:
            logger.warning(f"Initial activity failed: {e}")
