import asyncio
import random
import logging
from typing import Dict, Optional
from playwright.async_api import Page, BrowserContext
from .providers.sms.base import SMSProvider
from .utils.browser import create_stealth_context

logger = logging.getLogger(__name__)

class InstagramCreator:
    def __init__(self, sms_provider: SMSProvider, proxy_manager=None):
        self.sms_provider = sms_provider
        self.proxy_manager = proxy_manager

    async def human_type(self, page: Page, selector: str, text: str):
        """Types text with random delays between keystrokes."""
        await page.click(selector)
        for char in text:
            await page.type(selector, char, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.05, 0.1))

    async def register_account(self, context: BrowserContext, account_details: Dict[str, str]) -> bool:
        page = await context.new_page()
        try:
            logger.info(f"Attempting registration for {account_details['username']}")
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle")
            
            # Wait for form to load
            await page.wait_for_selector("input[name='emailOrPhone']")
            
            # Get Number from SMS Provider
            sms_data = await self.sms_provider.get_number()
            phone_number = sms_data['number']
            activation_id = sms_data['id']
            
            logger.info(f"Using phone number: {phone_number}")
            
            # Fill Registration Form
            await self.human_type(page, "input[name='emailOrPhone']", phone_number)
            await self.human_type(page, "input[name='fullName']", account_details['full_name'])
            await self.human_type(page, "input[name='username']", account_details['username'])
            await self.human_type(page, "input[name='password']", account_details['password'])
            
            # Click Sign Up
            await page.click("button[type='submit']")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Handling Birthday (IG often asks for this)
            if await page.query_selector("select[title='Month']"):
                await page.select_option("select[title='Month']", str(random.randint(1, 12)))
                await page.select_option("select[title='Day']", str(random.randint(1, 28)))
                await page.select_option("select[title='Year']", str(random.randint(1990, 2005)))
                await page.click("button:has-text('Next')")
                await asyncio.sleep(2)

            # OTP Verification
            logger.info("Waiting for OTP...")
            otp_code = None
            for _ in range(30):  # Wait up to 5 minutes (30 * 10s)
                otp_code = await self.sms_provider.get_otp(activation_id)
                if otp_code:
                    break
                await asyncio.sleep(10)
            
            if not otp_code:
                logger.error("OTP Timeout")
                await self.sms_provider.set_status(activation_id, 8) # Cancel
                return False
            
            logger.info(f"Received OTP: {otp_code}")
            await self.human_type(page, "input[name='email_confirmation_code']", otp_code)
            await page.click("button:has-text('Confirm')")
            
            await asyncio.sleep(5)
            # Verify if registration succeeded (check for URL change or profile element)
            if "accounts/emailsignup" not in page.url:
                logger.info("Account created successfully!")
                await self.sms_provider.set_status(activation_id, 6) # Complete
                return True
            
            return False

        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False
        finally:
            await page.close()
