"""
Redis configuration settings.
"""

import os

from dotenv import load_dotenv
load_dotenv()

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Connection settings
REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
REDIS_RETRY_ON_TIMEOUT = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '10'))

# Default TTL settings (in seconds)
DEFAULT_TTL = int(os.getenv('REDIS_DEFAULT_TTL', '3600'))  # 1 hour
CACHE_TTL = int(os.getenv('REDIS_CACHE_TTL', '1800'))  # 30 minutes
SESSION_TTL = int(os.getenv('REDIS_SESSION_TTL', '86400'))  # 24 hours


def get_redis_config() -> dict:
    """
    Get Redis configuration as a dictionary.
    
    Returns:
        dict: Redis configuration parameters
    """
    config = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': REDIS_DB,
        'socket_timeout': REDIS_SOCKET_TIMEOUT,
        'socket_connect_timeout': REDIS_SOCKET_CONNECT_TIMEOUT,
        'retry_on_timeout': REDIS_RETRY_ON_TIMEOUT,
        'max_connections': REDIS_MAX_CONNECTIONS,
    }
    
    if REDIS_PASSWORD:
        config['password'] = REDIS_PASSWORD
    
    return config 
