"""
Elasticsearch configuration settings.
"""

import os
from typing import Optional, List

from dotenv import load_dotenv
load_dotenv()

# Elasticsearch Configuration
ELASTICSEARCH_HOSTS = os.getenv('ELASTICSEARCH_HOSTS_READ', None)
ELASTICSEARCH_USERNAME = os.getenv('ELASTICSEARCH_USERNAME', None)
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', None)
ELASTICSEARCH_TIMEOUT = int(os.getenv('ELASTICSEARCH_TIMEOUT', '30'))
ELASTICSEARCH_MAX_RETRIES = int(os.getenv('ELASTICSEARCH_MAX_RETRIES', '5'))

# SSL Configuration
ELASTICSEARCH_VERIFY_CERTS = os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
ELASTICSEARCH_SSL_SHOW_WARN = os.getenv('ELASTICSEARCH_SSL_SHOW_WARN', 'false').lower() == 'true'

# Default index configurations
DEFAULT_INDEX_CONFIG = os.getenv('ELASTICSEARCH_DEFAULT_INDEX_CONFIG', '{}')
DEFAULT_MAPPING_CONFIG = os.getenv('ELASTICSEARCH_DEFAULT_MAPPING_CONFIG', '{}')

# Search and indexing settings
DEFAULT_SEARCH_SIZE = int(os.getenv('ELASTICSEARCH_DEFAULT_SEARCH_SIZE', '10'))
DEFAULT_BULK_SIZE = int(os.getenv('ELASTICSEARCH_DEFAULT_BULK_SIZE', '1000'))
DEFAULT_REFRESH_INTERVAL = os.getenv('ELASTICSEARCH_DEFAULT_REFRESH_INTERVAL', '1s')

# Index naming patterns
INDEX_PREFIX = os.getenv('ELASTICSEARCH_INDEX_PREFIX', '')
INDEX_SUFFIX = os.getenv('ELASTICSEARCH_INDEX_SUFFIX', '')


def get_elastic_config() -> dict:
    """
    Get Elasticsearch configuration as a dictionary.
    
    Returns:
        dict: Elasticsearch configuration parameters
    """
    # Parse hosts - can be comma-separated string or single host
    hosts = ELASTICSEARCH_HOSTS
    if ',' in hosts:
        hosts = [host.strip() for host in hosts.split(',')]
    
    return {
        'hosts': hosts,
        'username': ELASTICSEARCH_USERNAME,
        'password': ELASTICSEARCH_PASSWORD,
        'max_retries': ELASTICSEARCH_MAX_RETRIES,
        'verify_certs': ELASTICSEARCH_VERIFY_CERTS,
        'ssl_show_warn': ELASTICSEARCH_SSL_SHOW_WARN
    }


def get_elastic_config_with_custom_retries(max_retries: int) -> dict:
    """
    Get Elasticsearch configuration with custom max retries.
    
    Args:
        max_retries: Custom maximum retry attempts
        
    Returns:
        dict: Elasticsearch configuration parameters with custom max retries
    """
    config = get_elastic_config()
    config['max_retries'] = max_retries
    return config


def get_elastic_config_with_ssl(verify_certs: bool = True, ssl_show_warn: bool = True) -> dict:
    """
    Get Elasticsearch configuration with SSL settings.
    
    Args:
        verify_certs: Whether to verify SSL certificates
        ssl_show_warn: Whether to show SSL warnings
        
    Returns:
        dict: Elasticsearch configuration parameters with SSL settings
    """
    config = get_elastic_config()
    config['verify_certs'] = verify_certs
    config['ssl_show_warn'] = ssl_show_warn
    return config
