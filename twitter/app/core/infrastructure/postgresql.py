"""
PostgreSQL infrastructure management for the Telegram application.

This module handles PostgreSQL setup and configuration.
"""

import logging
from typing import Dict, Any
from sqlalchemy import create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


class PostgreSQLInfrastructure:
    """Manages PostgreSQL infrastructure setup and teardown."""
    
    def __init__(self):
        self.engine = None
    
    async def setup(self) -> bool:
        """Complete PostgreSQL infrastructure setup."""
        try:
            # Create PostgreSQL engine
            self.engine = create_engine(
                f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )
            
            logger.info("PostgreSQL infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL infrastructure: {e}")
            return False
    
    def get_engine(self):
        """Get the PostgreSQL engine instance."""
        return self.engine
