from abc import ABC, abstractmethod
from typing import Dict, Optional

class SMSProvider(ABC):
    """Abstract base class for SMS providers."""

    @abstractmethod
    async def get_number(self) -> Dict[str, str]:
        """
        Request a phone number for Instagram.
        Returns a dict with 'id' and 'number'.
        """
        pass

    async def register_phone(self, phone: str, tab_id: int) -> Dict[str, str]:
        """
        Register an explicit pre-assigned phone for a tab.
        Default implementation falls back to get_number().
        ManualOTPProvider overrides this for direct assignment.
        """
        return await self.get_number()

    @abstractmethod
    async def get_otp(self, activation_id: str) -> Optional[str]:
        """
        Get the OTP code for a given activation ID.
        Returns the code string if received, else None.
        """
        pass

    @abstractmethod
    async def set_status(self, activation_id: str, status: int) -> bool:
        """
        Set the status for an activation (e.g., ready, complete, cancel).
        Returns True if successful.
        """
        pass
