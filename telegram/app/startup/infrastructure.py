"""
Infrastructure startup module for the Telegram application.

This module handles the initialization of all infrastructure components.
"""

import random
import socks
import logging
from typing import Dict, Any

from app.core.config import settings
from app.core.infrastructure.kafka import KafkaInfrastructure
from app.core.infrastructure.elasticsearch import ElasticsearchInfrastructure
from app.core.infrastructure.minio import MinIOInfrastructure
from app.core.infrastructure.redis import RedisInfrastructure
from app.core.infrastructure.postgresql import PostgreSQLInfrastructure

logger = logging.getLogger(__name__)

# Global infrastructure instances
kafka_infrastructure = None
elasticsearch_infrastructure = None
minio_infrastructure = None
redis_infrastructure = None
postgresql_infrastructure = None
proxy_server = None


def print_startup_banner():
    """Print the startup banner."""
    random.seed(43)
    colors = ['\033[31m', '\033[32m', '\033[33m', '\033[34m', '\033[35m', '\033[36m']
    n = '\033[0m'
    b = [
        '░██████╗███████╗████████╗██╗░░░██╗██████╗░',
        '██╔════╝██╔════╝╚══██╔══╝██║░░░██║██╔══██╗',
        '╚█████╗░█████╗░░░░░██║░░░██║░░░██║██████╔╝',
        '░╚═══██╗██╔══╝░░░░░██║░░░██║░░░██║██╔═══╝░',
        '██████╔╝███████╗░░░██║░░░╚██████╔╝██║░░░░░',
        '╚═════╝░╚══════╝░░░╚═╝░░░░╚═════╝░╚═╝░░░░░',
    ]
    for char in b:
        print(f'{random.choice(colors)}{char}{n}')


async def setup_kafka() -> bool:
    """Setup Kafka infrastructure."""
    global kafka_infrastructure
    
    try:
        kafka_infrastructure = KafkaInfrastructure()
        success = await kafka_infrastructure.setup()
        if success:
            logger.info("Kafka infrastructure setup completed")
        return success
    except Exception as e:
        logger.error(f"Failed to setup Kafka infrastructure: {e}")
        return False


async def kafka_create_middle_connectors(connectors=[]) -> bool:
    """Create middle connectors for Kafka."""
    global kafka_infrastructure
    
    try:
        success = await kafka_infrastructure.create_middle_connectors(connectors=connectors)
        if success:
            logger.info("Kafka middle connectors created")
        return success
    except Exception as e:
        logger.error(f"Failed to create Kafka middle connectors: {e}")
        return False


async def kafka_wait_for_middle_topics(topics=[]) -> bool:
    """Wait for Kafka middle topics to be available."""
    global kafka_infrastructure
    return await kafka_infrastructure.wait_for_middle_topics(topics=topics)


async def kafka_create_middle_streams(streams=[]) -> bool:
    """Create middle streams for Kafka."""
    global kafka_infrastructure
    return await kafka_infrastructure.create_middle_streams(streams=streams)


async def setup_elasticsearch() -> bool:
    """Setup Elasticsearch infrastructure."""
    global elasticsearch_infrastructure
    
    try:
        elasticsearch_infrastructure = ElasticsearchInfrastructure()
        success = await elasticsearch_infrastructure.setup()
        if success:
            logger.info("Elasticsearch infrastructure setup completed")
        return success
    except Exception as e:
        logger.error(f"Failed to setup Elasticsearch infrastructure: {e}")
        return False


async def setup_minio() -> bool:
    """Setup MinIO infrastructure."""
    global minio_infrastructure
    
    try:
        minio_infrastructure = MinIOInfrastructure()
        success = await minio_infrastructure.setup()
        if success:
            logger.info("MinIO infrastructure setup completed")
        return success
    except Exception as e:
        logger.error(f"Failed to setup MinIO infrastructure: {e}")
        return False


async def setup_redis() -> bool:
    """Setup Redis infrastructure."""
    global redis_infrastructure
    
    try:
        redis_infrastructure = RedisInfrastructure()
        success = await redis_infrastructure.setup()
        if success:
            logger.info("Redis infrastructure setup completed")
        return success
    except Exception as e:
        logger.error(f"Failed to setup Redis infrastructure: {e}")
        return False


async def setup_postgresql() -> bool:
    """Setup PostgreSQL infrastructure."""
    global postgresql_infrastructure
    
    try:
        postgresql_infrastructure = PostgreSQLInfrastructure()
        success = await postgresql_infrastructure.setup()
        if success:
            logger.info("PostgreSQL infrastructure setup completed")
        return success
    except Exception as e:
        logger.error(f"Failed to setup PostgreSQL infrastructure: {e}")
        return False


def setup_proxy():
    """Setup proxy server configuration."""
    global proxy_server
    
    try:
        proxy_server = (
            socks.SOCKS5 if settings.PROXY_PROTOCOL == "socks5h" else socks.HTTP,
            settings.PROXY_HOST,
            settings.PROXY_PORT,
            True,
        )
        logger.info("Proxy server configuration completed")
        return True
    except Exception as e:
        logger.error(f"Failed to setup proxy server: {e}")
        return False


async def setup_all_infrastructure() -> bool:
    """Setup all infrastructure components."""
    print_startup_banner()
    
    logger.info("Starting infrastructure setup...")
    
    # Setup proxy first (synchronous)
    if not setup_proxy():
        return False
    
    # Setup all infrastructure components
    infrastructure_setup_functions = [
        setup_kafka,
        setup_elasticsearch,
        setup_minio,
        setup_redis,
        setup_postgresql,
    ]
    
    for setup_func in infrastructure_setup_functions:
        if not await setup_func():
            logger.error(f"Infrastructure setup failed at {setup_func.__name__}")
            return False
    
    logger.info("All infrastructure components setup completed successfully")
    return True


# Exported infrastructure instances
def get_kafka_handler():
    """Get Kafka handler instance."""
    return kafka_infrastructure.get_handler() if kafka_infrastructure else None


def get_elasticsearch_handler():
    """Get Elasticsearch handler instance."""
    return elasticsearch_infrastructure.get_handler() if elasticsearch_infrastructure else None


def get_minio_handler():
    """Get MinIO handler instance."""
    return minio_infrastructure.get_handler() if minio_infrastructure else None


def get_redis_handler():
    """Get Redis handler instance."""
    return redis_infrastructure.get_handler() if redis_infrastructure else None


def get_postgresql_engine():
    """Get PostgreSQL engine instance."""
    return postgresql_infrastructure.get_engine() if postgresql_infrastructure else None


def get_proxy_server():
    """Get proxy server configuration."""
    return proxy_server


# Exported symbols for backward compatibility
__all__ = [
    "setup_all_infrastructure",
    "get_kafka_handler",
    "kafka_create_middle_connectors",
    # "kafka_delete_middle_connectors",
    "kafka_wait_for_middle_topics",
    "kafka_create_middle_streams",
    "get_elasticsearch_handler", 
    "get_minio_handler",
    "get_redis_handler",
    "get_postgresql_engine",
    "get_proxy_server",
    "proxy_server",
    "ksql_handler",
    "elastic_handler",
    "minio_handler",
    "redis_handler",
    "postgres_engine",
    "create_elasticsearch_indexes",
]

# Backward compatibility aliases
ksql_handler = get_kafka_handler
elastic_handler = get_elasticsearch_handler
minio_handler = get_minio_handler
redis_handler = get_redis_handler
postgres_engine = get_postgresql_engine

async def create_elasticsearch_indexes():
    """Create Elasticsearch indexes - backward compatibility function."""
    return await setup_elasticsearch()
