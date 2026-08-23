"""
Elasticsearch infrastructure management for the Telegram application.

This module handles Elasticsearch setup and index creation.
"""

import logging
from typing import List, Dict, Any

from utils.elastic_handler import ElasticHandler
from utils.elastic_config import get_elastic_config
from app.core.config.elasticsearch_configs import ELASTICSEARCH_INDEX_DEFINITIONS

logger = logging.getLogger(__name__)


class ElasticsearchInfrastructure:
    """Manages Elasticsearch infrastructure setup and teardown."""
    
    def __init__(self):
        self.elastic_config = get_elastic_config()
        self.elastic_handler = ElasticHandler(**self.elastic_config)
    
    async def create_indexes(self) -> bool:
        """Create Elasticsearch indexes from configuration."""
        logger.info("Creating Elasticsearch indexes...")
        
        try:
            for index in ELASTICSEARCH_INDEX_DEFINITIONS:
                await self.elastic_handler.create_index(
                    index_name=index['name'], 
                    body=index['config'], 
                    check_exists=True
                )
                logger.info(f"Created/verified index: {index['name']}")
            
            logger.info("Elasticsearch indexes setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Elasticsearch indexes: {e}")
            return False
    
    async def setup(self) -> bool:
        """Complete Elasticsearch infrastructure setup."""
        try:
            if not await self.create_indexes():
                return False
            
            logger.info("Elasticsearch infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Elasticsearch infrastructure: {e}")
            return False
    
    def get_handler(self) -> ElasticHandler:
        """Get the Elasticsearch handler instance."""
        return self.elastic_handler
