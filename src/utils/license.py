import aiohttp
import logging
import sys
import random
import asyncio

logger = logging.getLogger("License")

class LicenseManager:
    """
    Manages remote script activation. 
    Can be used to remotely disable the script if payment is not received.
    """
    
    def __init__(self, status_url: str):
        self.status_url = status_url

    async def check_activation(self) -> bool:
        """
        Checks if the script is allowed to run.
        Returns True if ACTIVE, else simulates an error and exits.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.status_url, timeout=10) as response:
                    if response.status == 200:
                        status = (await response.text()).strip().upper()
                        if status == "ACTIVE":
                            return True
                        
            # If status is not ACTIVE or server returns error, simulate a fake system error
            self._simulate_fake_error()
            return False
            
        except Exception:
            # If internet is down or URL is wrong, we also stop for safety
            self._simulate_fake_error()
            return False

    def _simulate_fake_error(self):
        """Simulates a boring system/network error to avoid suspicion."""
        errors = [
            "ConnectionTimeout: Failed to establish a new connection: [Errno 60] Operation timed out",
            "SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed",
            "RuntimeError: Failed to initialize Chromium context: Protocol error",
            "ImportError: libnss3.so: cannot open shared object file: No such file or directory"
        ]
        print(f"\n{random.choice(errors)}")
        sys.exit(1)
