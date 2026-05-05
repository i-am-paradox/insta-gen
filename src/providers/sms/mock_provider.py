import asyncio
import random
import logging
from typing import Dict, Optional
from src.providers.sms.base import SMSProvider

logger = logging.getLogger("MockSMS")


class MockSMSProvider(SMSProvider):
    """
    Simulates an SMS provider for testing purposes.
    No API keys required. Generates unique numbers per call.
    """

    def __init__(self):
        self._counter = 0
        self._otp_store: Dict[str, str] = {}

    async def get_number(self) -> Dict[str, str]:
        self._counter += 1
        # Generate unique phone number each time
        suffix = f"{random.randint(10000, 99999)}{self._counter:03d}"
        number = f"+91{suffix[:10]}"
        act_id = f"mock_{self._counter}_{random.randint(1000, 9999)}"

        # Pre-generate OTP for this activation
        otp = str(random.randint(100000, 999999))
        self._otp_store[act_id] = otp

        logger.info(f"📱 Mock number #{self._counter}: {number} (OTP will be: {otp})")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        return {"id": act_id, "number": number}

    async def get_otp(self, activation_id: str) -> Optional[str]:
        logger.info(f"📨 Mock: Checking OTP for {activation_id}...")
        # Simulate 2s network delay then return OTP
        await asyncio.sleep(2)
        otp = self._otp_store.get(activation_id, "123456")
        logger.info(f"✅ Mock OTP received: {otp}")
        return otp

    async def set_status(self, activation_id: str, status: int) -> bool:
        status_names = {6: "COMPLETE", 8: "CANCEL"}
        name = status_names.get(status, f"STATUS_{status}")
        logger.info(f"📋 Mock: Status set to {name} for {activation_id}")
        # Cleanup
        self._otp_store.pop(activation_id, None)
        return True