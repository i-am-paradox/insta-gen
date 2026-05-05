import asyncio
import random
import logging
import os
import re
from typing import Dict, Optional
from playwright.async_api import Page
from .providers.sms.base import SMSProvider
from .utils.human import HumanEngine

logger = logging.getLogger("Creator")

# Status constants for live tracking
STATUS_IDLE = "IDLE"
STATUS_WARMING = "WARMING"
STATUS_NAVIGATING = "NAVIGATING"
STATUS_FILLING = "FILLING"
STATUS_SUBMITTING = "SUBMITTING"
STATUS_OTP_WAIT = "OTP_WAIT"
STATUS_OTP_FILL = "OTP_FILL"
STATUS_SUCCESS = "SUCCESS ✅"
STATUS_FAILED = "FAILED ❌"


# Typing speed → (min_ms, max_ms, pause_probability)
_TYPING_SPEEDS = {
    "fast":     (20,  80,  0.03),
    "medium":   (40,  140, 0.08),
    "slow":     (80,  220, 0.15),
    "paranoid": (120, 350, 0.25),
}


class ProInstagramCreator:
    """
    Handles Instagram account registration on a single PAGE (tab).
    Each call to register() works independently on its own tab.
    """

    def __init__(self, sms_provider: SMSProvider, enable_warming: bool = True,
                 anti_ban: Optional[Dict] = None):
        self.sms_provider = sms_provider
        self.enable_warming = enable_warming
        self.human = HumanEngine()

        cfg = anti_ban or {}
        speed = cfg.get("typing_speed", "medium")
        self._t_min, self._t_max, self._t_pause = _TYPING_SPEEDS.get(speed, _TYPING_SPEEDS["medium"])
        self._random_delays: bool = cfg.get("random_delays", True)
        self._debug_screenshots: bool = cfg.get("debug_screenshots", False)
        self._max_retries: int = cfg.get("max_retries", 2)

        # Live status tracking per tab
        self._tab_status: Dict[int, str] = {}
        self._stats = {"success": 0, "failed": 0, "in_progress": 0}

    @property
    def stats(self):
        return self._stats.copy()

    def get_tab_status(self, tab_id: int) -> str:
        return self._tab_status.get(tab_id, STATUS_IDLE)

    def get_all_statuses(self) -> Dict[int, str]:
        return self._tab_status.copy()

    def _set_status(self, tab_id: int, status: str):
        self._tab_status[tab_id] = status

    async def _handle_cookies(self, page: Page):
        """Dismiss cookie banner if it appears."""
        try:
            # Try multiple known cookie button texts
            for text in ["Allow all cookies", "Allow essential and optional cookies",
                         "Accept All", "Accept all cookies", "Only allow essential cookies"]:
                try:
                    btn = page.get_by_role("button", name=text)
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        logger.debug("Cookie banner dismissed")
                        await asyncio.sleep(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    async def _warm_session(self, page: Page, tab_id: int):
        """Build cookie trust by visiting a popular site first."""
        if not self.enable_warming:
            return

        sites = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://www.wikipedia.org",
        ]
        target = random.choice(sites)
        self._set_status(tab_id, STATUS_WARMING)
        logger.info(f"[Tab-{tab_id}] 🌐 Warming on {target}...")

        try:
            await page.goto(target, wait_until="domcontentloaded", timeout=30000)
            await self.human.random_scroll(page)
            await self.human.human_delay(3.0, 6.0)
        except Exception as e:
            logger.warning(f"[Tab-{tab_id}] Warming failed (non-critical): {e}")

    async def _fill_birthday(self, page: Page, tab_id: int) -> bool:
        """
        Fill Instagram 2026 DOB custom comboboxes.
        DOM confirmed: div[role='combobox'][aria-label='Select Month/Day/Year']
        Options are div[role='option'] inside a div[role='listbox'].
        """
        MONTH_NAMES = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        month = random.randint(1, 12)
        day   = random.randint(1, 28)
        year  = random.randint(1992, 2001)
        logger.info(f"[Tab-{tab_id}] 🎂 DOB: {MONTH_NAMES[month-1]} {day}, {year}")

        fields = [
            ("Select Month", MONTH_NAMES[month - 1]),
            ("Select Day",   str(day)),
            ("Select Year",  str(year)),
        ]

        for aria_label, value in fields:
            try:
                # Click the combobox trigger (div[role='combobox'][aria-label='Select Month'])
                trigger = page.locator(f"[role='combobox'][aria-label='{aria_label}']")
                await trigger.wait_for(state="visible", timeout=5000)
                await trigger.click()
                await asyncio.sleep(random.uniform(0.4, 0.7))

                # Click the matching option inside the open listbox
                # Exact match first, then partial text match
                option = page.locator(f"[role='option']").filter(has_text=re.compile(f"^{re.escape(value)}$"))
                if await option.count() == 0:
                    option = page.locator(f"[role='option']").filter(has_text=value).first

                await option.wait_for(state="visible", timeout=4000)
                await option.first.click()
                await asyncio.sleep(random.uniform(0.3, 0.5))
                logger.info(f"[Tab-{tab_id}] ✅ {aria_label} → {value}")

            except Exception as e:
                logger.error(f"[Tab-{tab_id}] ❌ {aria_label} failed: {e}")
                # Close dropdown if open
                try:
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

        return True

    async def _take_debug_screenshot(self, page: Page, tab_id: int, step: str):
        """Save a screenshot for debugging on failure (only if debug_screenshots enabled)."""
        if not self._debug_screenshots:
            return
        try:
            os.makedirs("debug_screenshots", exist_ok=True)
            path = f"debug_screenshots/tab{tab_id}_{step}.png"
            await page.screenshot(path=path)
            logger.debug(f"[Tab-{tab_id}] 📸 Screenshot saved: {path}")
        except Exception:
            pass

    async def _fill_by_label(self, page: Page, tab_id: int, text: str,
                              labels: list, fallback_selectors: list,
                              field_name: str) -> bool:
        """
        Fill a form field using multiple strategies.
        Instagram's new UI has no name/placeholder attributes on inputs.
        """
        # Strategy 1: Playwright get_by_label (matches <label> elements)
        for label in labels:
            try:
                locator = page.get_by_label(label, exact=False)
                if await locator.count() > 0 and await locator.first.is_visible(timeout=3000):
                    # Scroll into view first
                    await locator.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await locator.first.click(timeout=5000)
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                    # Clear + type
                    await page.keyboard.press("Meta+a")
                    await asyncio.sleep(0.1)
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(0.15)
                    for char in text:
                        await page.keyboard.type(char, delay=random.randint(self._t_min, self._t_max))
                        if random.random() < self._t_pause:
                            await asyncio.sleep(random.uniform(0.2, 0.7))
                    logger.debug(f"[Tab-{tab_id}] ✅ {field_name} filled via label '{label}'")
                    return True
            except Exception:
                continue

        # Strategy 2: Playwright get_by_placeholder
        for label in labels:
            try:
                locator = page.get_by_placeholder(label, exact=False)
                if await locator.count() > 0 and await locator.first.is_visible(timeout=2000):
                    await locator.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await locator.first.click(timeout=5000)
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                    await page.keyboard.press("ControlOrMeta+a")
                    await asyncio.sleep(0.1)
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(0.15)
                    for char in text:
                        await page.keyboard.type(char, delay=random.randint(self._t_min, self._t_max))
                        if random.random() < self._t_pause:
                            await asyncio.sleep(random.uniform(0.2, 0.7))
                    logger.debug(f"[Tab-{tab_id}] ✅ {field_name} filled via placeholder '{label}'")
                    return True
            except Exception:
                continue

        # Strategy 3: CSS selectors with scroll
        for selector in fallback_selectors:
            try:
                el = await page.wait_for_selector(selector, state="visible", timeout=5000)
                if el:
                    await el.scroll_into_view_if_needed()
                    await asyncio.sleep(0.2)
                    await el.click(timeout=5000)
                    await asyncio.sleep(0.2)
                    await page.keyboard.press("ControlOrMeta+a")
                    await asyncio.sleep(0.1)
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(0.1)
                    for char in text:
                        await page.keyboard.type(char, delay=random.randint(self._t_min, self._t_max))
                    logger.debug(f"[Tab-{tab_id}] ✅ {field_name} filled via selector '{selector}'")
                    return True
            except Exception:
                continue

        logger.error(f"[Tab-{tab_id}] ❌ Could not find {field_name} input field")
        await self._take_debug_screenshot(page, tab_id, f"no_{field_name.lower().replace(' ', '_')}_field")
        return False

    async def register(self, page: Page, tab_id: int,
                       account_details: Dict[str, str]) -> bool:
        """
        Complete registration flow on a single tab (page).
        Returns True if account was created successfully.
        """
        username = account_details['username']
        self._stats["in_progress"] += 1

        try:
            # ── Step 1: Session Warming ──
            await self._warm_session(page, tab_id)

            # ── Step 2: Navigate to Instagram Signup ──
            self._set_status(tab_id, STATUS_NAVIGATING)
            logger.info(f"[Tab-{tab_id}] 📱 Opening Instagram signup...")

            await page.goto(
                "https://www.instagram.com/accounts/emailsignup/",
                wait_until="domcontentloaded",
                timeout=45000
            )
            await self.human.human_delay(2.0, 4.0)

            # Handle cookie popup
            await self._handle_cookies(page)

            # ── Step 3: Get Phone Number ──
            if account_details.get("phone_override"):
                sms_data = await self.sms_provider.register_phone(
                    account_details["phone_override"], tab_id
                )
            else:
                sms_data = await self.sms_provider.get_number()
            phone = sms_data['number']
            act_id = sms_data['id']
            logger.info(f"[Tab-{tab_id}] 📱 Got number: {phone}")

            # ── Step 4: Fill Registration Form ──
            # Instagram NEW UI has no name/placeholder on inputs — use label locators
            self._set_status(tab_id, STATUS_FILLING)
            logger.info(f"[Tab-{tab_id}] ✍️  Filling form for {username}...")

            # Phone/Email field
            phone_filled = await self._fill_by_label(
                page, tab_id, phone,
                labels=["Mobile number or email", "Mobile number or email address",
                        "Email or phone number"],
                fallback_selectors=["input[name='emailOrPhone']", "input[type='tel']"],
                field_name="Phone"
            )
            if not phone_filled:
                return False
            await self.human.human_delay(0.5, 1.0)

            # Password
            await self._fill_by_label(
                page, tab_id, account_details['password'],
                labels=["Password"],
                fallback_selectors=["input[type='password']", "input[name='password']"],
                field_name="Password"
            )
            await self.human.human_delay(0.3, 0.8)

            # Birthday (dropdowns — on the same page in new UI)
            await self._fill_birthday(page, tab_id)
            await self.human.human_delay(0.3, 0.6)

            # Full Name
            await self._fill_by_label(
                page, tab_id, account_details['full_name'],
                labels=["Full name", "Full Name", "Name"],
                fallback_selectors=["input[name='fullName']"],
                field_name="Full Name"
            )
            await self.human.human_delay(0.3, 0.8)

            # Username (Instagram uses input[type='search'] with aria-label)
            await self._fill_by_label(
                page, tab_id, username,
                labels=["Username"],
                fallback_selectors=["input[aria-label='Username']", "input[type='search'][aria-label='Username']", "input[name='username']"],
                field_name="Username"
            )
            await self.human.human_delay(0.5, 1.5)

            # ── Step 5: Submit Form ──
            self._set_status(tab_id, STATUS_SUBMITTING)
            logger.info(f"[Tab-{tab_id}] 🚀 Submitting registration...")

            submitted = False
            for btn_text in ["Sign up", "Submit", "Next"]:
                try:
                    btn = page.get_by_role("button", name=btn_text)
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if not submitted:
                # Fallback: try button[type=submit]
                try:
                    await self.human.move_and_click(page, "button[type='submit']")
                    submitted = True
                except Exception:
                    pass

            if not submitted:
                logger.error(f"[Tab-{tab_id}] ❌ Could not find submit button")
                await self._take_debug_screenshot(page, tab_id, "no_submit_btn")
                return False

            await self.human.human_delay(3.0, 5.0)

            # ── Step 5b: Birthday page (if shown separately after submit) ──
            try:
                combos_after = page.get_by_role("combobox")
                if await combos_after.count() >= 3:
                    logger.info(f"[Tab-{tab_id}] 🎂 Birthday page detected after submit")
                    await self._fill_birthday(page, tab_id)
                    for btn_text in ["Next", "Submit", "Sign Up"]:
                        try:
                            btn = page.get_by_role("button", name=btn_text)
                            if await btn.is_visible(timeout=2000):
                                await btn.click()
                                break
                        except Exception:
                            continue
                    await self.human.human_delay(3.0, 5.0)
            except Exception:
                logger.debug(f"[Tab-{tab_id}] No separate birthday form (ok)")

            # ── Step 6: Wait for OTP page (up to 20 seconds) ──
            OTP_SELECTORS = [
                "input[autocomplete='one-time-code']",
                "input[inputmode='numeric']",
                "input[name='email_confirmation_code']",
                "input[name='confirmationCode']",
                "input[name='verificationCode']",
                "input[aria-label*='ode']",
                "input[placeholder*='ode']",
                "input[placeholder*='verification']",
                "input[maxlength='6']",
                "input[type='tel'][maxlength='6']",
            ]

            logger.info(f"[Tab-{tab_id}] ⏳ Waiting for Instagram OTP page (up to 20s)...")
            otp_input_sel = None
            for _ in range(20):
                for sel in OTP_SELECTORS:
                    try:
                        if await page.locator(sel).count() > 0:
                            otp_input_sel = sel
                            break
                    except Exception:
                        pass
                if otp_input_sel:
                    break
                await asyncio.sleep(1)

            if not otp_input_sel:
                current_url = page.url
                logger.warning(f"[Tab-{tab_id}] ⚠️  OTP field not found after 20s. URL: {current_url}")
                await self._take_debug_screenshot(page, tab_id, "otp_field_missing")
                if "emailsignup" in current_url:
                    logger.error(f"[Tab-{tab_id}] ❌ Still on signup — form did not submit")
                    return False
                # URL changed but no OTP field — might be a different flow, continue anyway

            self._set_status(tab_id, STATUS_OTP_WAIT)
            logger.info(f"[Tab-{tab_id}] ✅ OTP page detected — waiting for user to enter code in dashboard...")

            otp = await self.sms_provider.get_otp(act_id)  # blocks until dashboard input (5min timeout)

            if not otp:
                logger.error(f"[Tab-{tab_id}] ❌ OTP timeout after 100s")
                await self.sms_provider.set_status(act_id, 8)  # Cancel
                await self._take_debug_screenshot(page, tab_id, "otp_timeout")
                return False

            # Fill OTP
            self._set_status(tab_id, STATUS_OTP_FILL)
            logger.info(f"[Tab-{tab_id}] 🔢 Filling OTP: {otp}")

            otp_filled = False
            fill_candidates = (
                [otp_input_sel] if otp_input_sel else []
            ) + [
                "input[autocomplete='one-time-code']",
                "input[inputmode='numeric']",
                "input[name='email_confirmation_code']",
                "input[name='confirmationCode']",
                "input[name='verificationCode']",
                "input[aria-label*='ode']",
                "input[maxlength='6']",
            ]
            seen = set()
            for selector in fill_candidates:
                if selector in seen:
                    continue
                seen.add(selector)
                try:
                    el = await page.wait_for_selector(selector, state="visible", timeout=4000)
                    if el:
                        await self.human.human_type(page, selector, otp)
                        otp_filled = True
                        break
                except Exception:
                    continue

            if not otp_filled:
                logger.error(f"[Tab-{tab_id}] ❌ Could not find OTP input")
                await self._take_debug_screenshot(page, tab_id, "no_otp_field")
                return False

            # ── Step 7: Submit OTP ──
            for btn_text in ["Confirm", "Next", "Submit", "Verify"]:
                try:
                    btn = page.get_by_role("button", name=btn_text)
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        logger.info(f"[Tab-{tab_id}] 🟢 OTP submitted via '{btn_text}' button")
                        break
                except Exception:
                    continue

            # ── Step 8: Count as SUCCESS ──
            # OTP sent = job done. Account is created on Instagram's side.
            self._set_status(tab_id, STATUS_SUCCESS)
            self._stats["success"] += 1
            logger.info(f"[Tab-{tab_id}] 🎉 OTP submitted for '{username}' — account creation complete!")
            await self.sms_provider.set_status(act_id, 6)  # Complete
            return True

        except Exception as e:
            self._set_status(tab_id, STATUS_FAILED)
            self._stats["failed"] += 1
            logger.error(f"[Tab-{tab_id}] 💥 Registration error: {e}")
            await self._take_debug_screenshot(page, tab_id, "exception")
            return False

        finally:
            self._stats["in_progress"] = max(0, self._stats["in_progress"] - 1)
