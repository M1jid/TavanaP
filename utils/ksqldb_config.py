"""
ksqlDB configuration settings.
"""

import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

# ksqlDB Configuration
KSQLDB_URL = os.getenv('KSQLDB_URL', None)
KSQLDB_TIMEOUT = int(os.getenv('KSQLDB_TIMEOUT', None))
KSQLDB_MAX_RETRIES = int(os.getenv('KSQLDB_MAX_RETRIES', None))

# Default stream and table configurations
DEFAULT_STREAM_CONFIG = os.getenv('KSQLDB_DEFAULT_STREAM_CONFIG', '')
DEFAULT_TABLE_CONFIG = os.getenv('KSQLDB_DEFAULT_TABLE_CONFIG', '')

# Default connector configurations
DEFAULT_SINK_CONNECTOR_CONFIG = os.getenv('KSQLDB_DEFAULT_SINK_CONNECTOR_CONFIG', '')
DEFAULT_SOURCE_CONNECTOR_CONFIG = os.getenv('KSQLDB_DEFAULT_SOURCE_CONNECTOR_CONFIG', '')

# Query timeout settings (in seconds)
DEFAULT_QUERY_TIMEOUT = int(os.getenv('KSQLDB_QUERY_TIMEOUT', '30'))
STREAM_QUERY_TIMEOUT = int(os.getenv('KSQLDB_STREAM_QUERY_TIMEOUT', '60'))
CONNECTOR_QUERY_TIMEOUT = int(os.getenv('KSQLDB_CONNECTOR_QUERY_TIMEOUT', '45'))


def get_ksqldb_config() -> dict:
    """
    Get ksqlDB configuration as a dictionary.
    
    Returns:
        dict: ksqlDB configuration parameters
    """
    return {
        'ksqldb_url': KSQLDB_URL,
        'timeout': KSQLDB_TIMEOUT,
        'max_retries': KSQLDB_MAX_RETRIES
    }


def get_ksqldb_config_with_custom_timeout(timeout: int) -> dict:
    """
    Get ksqlDB configuration with custom timeout.
    
    Args:
        timeout: Custom timeout in seconds
        
    Returns:
        dict: ksqlDB configuration parameters with custom timeout
    """
    config = get_ksqldb_config()
    config['timeout'] = timeout
    return config


def get_ksqldb_config_with_custom_retries(max_retries: int) -> dict:
    """
    Get ksqlDB configuration with custom max retries.
    
    Args:
        max_retries: Custom maximum retry attempts
        
    Returns:
        dict: ksqlDB configuration parameters with custom max retries
    """
    config = get_ksqldb_config()
    config['max_retries'] = max_retries
    return config 
