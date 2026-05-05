import random
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger("AvatarSource")

class AvatarSourcing:
    """Sours realistic AI-generated or high-quality avatars."""
    
    @staticmethod
    async def get_random_avatar_url() -> str:
        """Returns a URL to a random high-quality profile picture."""
        # Using ThisPersonDoesNotExist alternative or Unsplash for realistic faces
        seed = random.randint(1, 100000)
        return f"https://i.pravatar.cc/300?u={seed}"

    @staticmethod
    async def download_avatar(url: str, save_path: str = "avatar.jpg") -> bool:
        """Downloads the avatar for uploading."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return True
            return False
        except Exception as e:
            logger.error(f"Failed to download avatar: {e}")
            return False
