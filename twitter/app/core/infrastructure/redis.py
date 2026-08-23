"""
Redis infrastructure management for the Telegram application.

This module handles Redis setup and configuration.
"""

import logging
from typing import Dict, Any

from utils.redis_handler import RedisHandler
from utils.redis_config import get_redis_config

logger = logging.getLogger(__name__)


class RedisInfrastructure:
    """Manages Redis infrastructure setup and teardown."""
    
    def __init__(self):
        self.redis_config = get_redis_config()
        self.redis_handler = RedisHandler(**self.redis_config)
    
    async def setup(self) -> bool:
        """Complete Redis infrastructure setup."""
        try:
            # Redis setup logic can be added here if needed
            logger.info("Redis infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Redis infrastructure: {e}")
            return False
    
    def get_handler(self) -> RedisHandler:
        """Get the Redis handler instance."""
        return self.redis_handler
