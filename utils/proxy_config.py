"""
Proxy configuration settings for Xray proxy management.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Proxy Configuration
PROXY_ROTATION_ENABLED = os.getenv('PROXY_ROTATION_ENABLED', 'true').lower() == 'true'
PROXY_TIMEOUT = int(os.getenv('PROXY_TIMEOUT', '30'))
PROXY_MAX_RETRIES = int(os.getenv('PROXY_MAX_RETRIES', '3'))
PROXY_ROTATION_INTERVAL = int(os.getenv('PROXY_ROTATION_INTERVAL', '300'))  # 5 minutes

# Xray Configuration
XRAY_EXECUTABLE_PATH = os.getenv('XRAY_EXECUTABLE_PATH', None)
XRAY_CONFIGS = os.getenv('XRAY_CONFIGS', '').split(',') if os.getenv('XRAY_CONFIGS') else []
XRAY_CONFIG_DIR = os.getenv('XRAY_CONFIG_DIR', None)
XRAY_SOCKS_PORT = int(os.getenv('XRAY_SOCKS_PORT', None))
XRAY_HTTP_PORT = int(os.getenv('XRAY_HTTP_PORT', None))

# Proxy Health Check
PROXY_HEALTH_CHECK_URL = os.getenv('PROXY_HEALTH_CHECK_URL', 'https://httpbin.org/ip')
PROXY_HEALTH_CHECK_TIMEOUT = int(os.getenv('PROXY_HEALTH_CHECK_TIMEOUT', '10'))
PROXY_HEALTH_CHECK_INTERVAL = int(os.getenv('PROXY_HEALTH_CHECK_INTERVAL', '60'))  # 1 minute

# Proxy Pool Management
PROXY_POOL_SIZE = int(os.getenv('PROXY_POOL_SIZE', '5'))
PROXY_FAILURE_THRESHOLD = int(os.getenv('PROXY_FAILURE_THRESHOLD', '3'))
PROXY_RECOVERY_TIME = int(os.getenv('PROXY_RECOVERY_TIME', '600'))  # 10 minutes

def get_proxy_config() -> Dict:
    """
    Get proxy configuration as a dictionary.
    
    Returns:
        dict: Proxy configuration parameters
    """
    return {
        'rotation_enabled': PROXY_ROTATION_ENABLED,
        'timeout': PROXY_TIMEOUT,
        'max_retries': PROXY_MAX_RETRIES,
        'rotation_interval': PROXY_ROTATION_INTERVAL,
        'health_check_url': PROXY_HEALTH_CHECK_URL,
        'health_check_timeout': PROXY_HEALTH_CHECK_TIMEOUT,
        'health_check_interval': PROXY_HEALTH_CHECK_INTERVAL,
        'pool_size': PROXY_POOL_SIZE,
        'failure_threshold': PROXY_FAILURE_THRESHOLD,
        'recovery_time': PROXY_RECOVERY_TIME,
        'xray_executable_path': XRAY_EXECUTABLE_PATH,
        'xray_config_dir': XRAY_CONFIG_DIR,
        'xray_socks_port': XRAY_SOCKS_PORT,
        'xray_http_port': XRAY_HTTP_PORT
    }


def get_xray_configs() -> List[str]:
    """
    Get Xray proxy configuration files.
    
    Returns:
        List[str]: List of Xray configuration file names
    """
    if XRAY_CONFIGS and XRAY_CONFIGS[0]:
        return [config.strip() for config in XRAY_CONFIGS if config.strip()]
    else:
        return []


def get_xray_config_path(config_name: str) -> str:
    """
    Get full path to Xray configuration file.
    
    Args:
        config_name: Configuration file name
        
    Returns:
        str: Full path to configuration file
    """
    return os.path.join(XRAY_CONFIG_DIR, config_name)


def get_proxy_config_with_custom_timeout(timeout: int) -> Dict:
    """
    Get proxy configuration with custom timeout.
    
    Args:
        timeout: Custom timeout in seconds
        
    Returns:
        dict: Proxy configuration parameters with custom timeout
    """
    config = get_proxy_config()
    config['timeout'] = timeout
    return config


def get_proxy_config_with_custom_retries(max_retries: int) -> Dict:
    """
    Get proxy configuration with custom max retries.
    
    Args:
        max_retries: Custom maximum retry attempts
        
    Returns:
        dict: Proxy configuration parameters with custom max retries
    """
    config = get_proxy_config()
    config['max_retries'] = max_retries
    return config


def get_proxy_config_with_rotation(rotation_enabled: bool) -> Dict:
    """
    Get proxy configuration with custom rotation setting.
    
    Args:
        rotation_enabled: Whether to enable proxy rotation
        
    Returns:
        dict: Proxy configuration parameters with custom rotation setting
    """
    config = get_proxy_config()
    config['rotation_enabled'] = rotation_enabled
    return config


def validate_xray_config(config_name: str) -> bool:
    """
    Validate an Xray configuration file exists.
    
    Args:
        config_name: Xray configuration file name
        
    Returns:
        bool: True if configuration file exists
    """
    config_path = get_xray_config_path(config_name)
    return os.path.exists(config_path)


def get_combined_proxy_configs() -> Dict:
    """
    Get combined proxy configuration including Xray configs.
    
    Returns:
        dict: Complete proxy configuration
    """
    config = get_proxy_config()
    config['xray_configs'] = get_xray_configs()
    return config