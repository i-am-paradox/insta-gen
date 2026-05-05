import aiohttp
import logging
from typing import Dict, Optional
from .base import SMSProvider

logger = logging.getLogger(__name__)

class SmsActivateProvider(SMSProvider):
    """Implementation of SMS-Activate provider."""
    
    BASE_URL = "https://api.sms-activate.org/stubs/handler_api.php"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _request(self, params: dict) -> str:
        params["api_key"] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                return await response.text()

    async def get_number(self) -> Dict[str, str]:
        params = {
            "action": "getNumber",
            "service": "ig",
            "country": "0",  # Russia or change as needed
        }
        response = await self._request(params)
        # Expected response: ACCESS_NUMBER:$id:$number
        if response.startswith("ACCESS_NUMBER"):
            _, activation_id, number = response.split(":")
            return {"id": activation_id, "number": number}
        
        logger.error(f"Failed to get number: {response}")
        raise Exception(f"SMS-Activate error: {response}")

    async def get_otp(self, activation_id: str) -> Optional[str]:
        params = {
            "action": "getStatus",
            "id": activation_id,
        }
        response = await self._request(params)
        # Expected response: STATUS_OK:$code or STATUS_WAIT_CODE
        if response.startswith("STATUS_OK"):
            _, code = response.split(":")
            return code
        elif response == "STATUS_WAIT_CODE":
            return None
        
        logger.warning(f"Unexpected status for {activation_id}: {response}")
        return None

    async def set_status(self, activation_id: str, status: int) -> bool:
        params = {
            "action": "setStatus",
            "id": activation_id,
            "status": status,
        }
        response = await self._request(params)
        return response == "ACCESS_READY" or response == "ACCESS_RETRY_GET" or response == "ACCESS_ACTIVATION"
