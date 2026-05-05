import asyncio
import logging
from typing import Dict, Optional, List, Callable, Awaitable
from .base import SMSProvider

logger = logging.getLogger("ManualOTP")


class ManualOTPProvider(SMSProvider):
    """
    SMS Provider that uses client-provided phone numbers
    and waits for manual OTP input via the web UI.
    
    - get_number() picks the next number from the provided list.
    - get_otp() sends an event to the UI and blocks until the client enters the OTP.
    - set_status() is a no-op (no external SMS API involved).
    """

    def __init__(self, phone_numbers: List[str]):
        self._numbers: List[str] = list(phone_numbers)
        self._index: int = 0
        # Map activation_id -> asyncio.Future that resolves with the OTP string
        self._pending_otps: Dict[str, asyncio.Future] = {}
        # Map activation_id -> phone number
        self._activation_phones: Dict[str, str] = {}
        # Map activation_id -> tab_id (so UI can update the right tab card)
        self._activation_tabs: Dict[str, int] = {}
        # Callback to notify UI that OTP is needed
        self._otp_request_callback: Optional[Callable[[str, str, str], Awaitable[None]]] = None

    def set_otp_request_callback(self, callback: Callable[[str, str, str], Awaitable[None]]):
        """
        Register a callback: async fn(activation_id, phone_number, tab_id) 
        Called when the script needs an OTP from the user.
        """
        self._otp_request_callback = callback

    @property
    def remaining_numbers(self) -> int:
        return max(0, len(self._numbers) - self._index)

    @property
    def total_numbers(self) -> int:
        return len(self._numbers)

    async def get_number(self) -> Dict[str, str]:
        if self._index >= len(self._numbers):
            raise Exception("No more phone numbers available in the list")

        phone = self._numbers[self._index].strip()
        act_id = f"manual_{self._index}"
        self._activation_phones[act_id] = phone
        self._activation_tabs[act_id] = 0
        self._index += 1

        logger.info(f"📱 Using number #{self._index}: {phone}")
        await asyncio.sleep(0.1)
        return {"id": act_id, "number": phone}

    async def register_phone(self, phone: str, tab_id: int) -> Dict[str, str]:
        """
        Register an explicit pre-assigned phone for a specific tab.
        Does NOT consume from the sequential index — phone is already assigned.
        """
        safe = phone.replace("+", "").replace(" ", "").replace("-", "")
        act_id = f"t{tab_id}_{safe}"
        self._activation_phones[act_id] = phone
        self._activation_tabs[act_id] = tab_id
        logger.info(f"📱 Tab-{tab_id} registered phone: {phone} → id: {act_id}")
        return {"id": act_id, "number": phone}

    async def get_otp(self, activation_id: str) -> Optional[str]:
        """
        Request OTP from the UI and wait until the user enters it.
        Times out after 300 seconds (5 min).
        """
        phone = self._activation_phones.get(activation_id, "unknown")
        tab_id = self._activation_tabs.get(activation_id, 0)
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_otps[activation_id] = future

        # Notify UI that OTP is needed (pass tab_id so UI can update tab card)
        if self._otp_request_callback:
            await self._otp_request_callback(activation_id, phone, str(tab_id))

        logger.info(f"⏳ Waiting for manual OTP for {phone} (id: {activation_id})...")

        try:
            otp = await asyncio.wait_for(future, timeout=300)
            logger.info(f"✅ OTP received for {phone}: {otp}")
            return otp
        except asyncio.TimeoutError:
            logger.error(f"❌ OTP timeout for {phone} (5 min)")
            self._pending_otps.pop(activation_id, None)
            return None

    def submit_otp(self, activation_id: str, otp: str) -> bool:
        """Called by the server when user submits OTP from UI."""
        future = self._pending_otps.pop(activation_id, None)
        if future and not future.done():
            future.set_result(otp)
            return True
        logger.warning(f"No pending OTP request for {activation_id}")
        return False

    async def set_status(self, activation_id: str, status: int) -> bool:
        """No-op for manual provider."""
        status_names = {6: "COMPLETE", 8: "CANCEL"}
        name = status_names.get(status, f"STATUS_{status}")
        logger.info(f"📋 Manual: Status {name} for {activation_id}")
        self._pending_otps.pop(activation_id, None)
        return True
