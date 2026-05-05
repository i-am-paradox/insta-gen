import os
import logging
from typing import List, Optional, Dict
from itertools import cycle

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy rotation and formatting for Playwright."""

    def __init__(self, proxy_file: str):
        self.proxy_file = proxy_file
        self.proxies: List[Dict[str, str]] = self._load_proxies()
        self.proxy_pool = cycle(self.proxies) if self.proxies else None

    def _load_proxies(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.proxy_file):
            logger.warning(f"Proxy file {self.proxy_file} not found.")
            return []

        loaded_proxies = []
        with open(self.proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(':')
                proxy_dict = {}
                
                if len(parts) == 2:  # ip:port
                    proxy_dict = {"server": f"http://{parts[0]}:{parts[1]}"}
                elif len(parts) == 4:  # ip:port:user:pass
                    proxy_dict = {
                        "server": f"http://{parts[0]}:{parts[1]}",
                        "username": parts[2],
                        "password": parts[3]
                    }
                
                if proxy_dict:
                    loaded_proxies.append(proxy_dict)
        
        logger.info(f"Loaded {len(loaded_proxies)} proxies from {self.proxy_file}")
        return loaded_proxies

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Returns the next proxy in the cycle."""
        if not self.proxy_pool:
            return None
        return next(self.proxy_pool)

    def has_proxies(self) -> bool:
        return len(self.proxies) > 0
