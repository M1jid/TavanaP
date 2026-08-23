"""
Kafka configuration settings.
"""

import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

# Kafka Connection Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SECURITY_PROTOCOL = os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')
KAFKA_SASL_MECHANISM = os.getenv('KAFKA_SASL_MECHANISM', 'PLAIN')
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', None)
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', None)
KAFKA_SSL_CA_LOCATION = os.getenv('KAFKA_SSL_CA_LOCATION', None)
KAFKA_SSL_CERTIFICATE_LOCATION = os.getenv('KAFKA_SSL_CERTIFICATE_LOCATION', None)
KAFKA_SSL_KEY_LOCATION = os.getenv('KAFKA_SSL_KEY_LOCATION', None)

# Producer Configuration
KAFKA_PRODUCER_ACKS = os.getenv('KAFKA_PRODUCER_ACKS', 'all')
KAFKA_PRODUCER_RETRIES = int(os.getenv('KAFKA_PRODUCER_RETRIES', '3'))
KAFKA_PRODUCER_BATCH_SIZE = int(os.getenv('KAFKA_PRODUCER_BATCH_SIZE', '16384'))
KAFKA_PRODUCER_LINGER_MS = int(os.getenv('KAFKA_PRODUCER_LINGER_MS', '5'))
KAFKA_PRODUCER_BUFFER_MEMORY = int(os.getenv('KAFKA_PRODUCER_BUFFER_MEMORY', '33554432'))
KAFKA_PRODUCER_COMPRESSION_TYPE = os.getenv('KAFKA_PRODUCER_COMPRESSION_TYPE', 'snappy')

# Consumer Configuration
KAFKA_CONSUMER_GROUP_ID = os.getenv('KAFKA_CONSUMER_GROUP_ID', 'default-group')
KAFKA_CONSUMER_AUTO_OFFSET_RESET = os.getenv('KAFKA_CONSUMER_AUTO_OFFSET_RESET', 'latest')
KAFKA_CONSUMER_ENABLE_AUTO_COMMIT = os.getenv('KAFKA_CONSUMER_ENABLE_AUTO_COMMIT', 'true').lower() == 'true'
KAFKA_CONSUMER_AUTO_COMMIT_INTERVAL_MS = int(os.getenv('KAFKA_CONSUMER_AUTO_COMMIT_INTERVAL_MS', '1000'))
KAFKA_CONSUMER_SESSION_TIMEOUT_MS = int(os.getenv('KAFKA_CONSUMER_SESSION_TIMEOUT_MS', '30000'))
KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS = int(os.getenv('KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS', '3000'))
KAFKA_CONSUMER_MAX_POLL_RECORDS = int(os.getenv('KAFKA_CONSUMER_MAX_POLL_RECORDS', '500'))
KAFKA_CONSUMER_FETCH_MIN_BYTES = int(os.getenv('KAFKA_CONSUMER_FETCH_MIN_BYTES', '1'))
KAFKA_CONSUMER_FETCH_MAX_WAIT_MS = int(os.getenv('KAFKA_CONSUMER_FETCH_MAX_WAIT_MS', '500'))

# Event-driven Configuration
KAFKA_LISTENER_ENABLED = os.getenv('KAFKA_LISTENER_ENABLED', 'true').lower() == 'true'
KAFKA_LISTENER_TOPICS = os.getenv('KAFKA_LISTENER_TOPICS', 'telegram_jobs').split(',')
KAFKA_LISTENER_GROUP_ID = os.getenv('KAFKA_LISTENER_GROUP_ID', 'telegram-workers')
KAFKA_LISTENER_POLL_TIMEOUT = float(os.getenv('KAFKA_LISTENER_POLL_TIMEOUT', '1.0'))

# Error Handling Configuration
KAFKA_MAX_RETRIES = int(os.getenv('KAFKA_MAX_RETRIES', '3'))
KAFKA_RETRY_DELAY = float(os.getenv('KAFKA_RETRY_DELAY', '1.0'))
KAFKA_RETRY_BACKOFF = float(os.getenv('KAFKA_RETRY_BACKOFF', '2.0'))

# Serialization Configuration
KAFKA_KEY_SERIALIZER = os.getenv('KAFKA_KEY_SERIALIZER', 'json')  # json, string, bytes
KAFKA_VALUE_SERIALIZER = os.getenv('KAFKA_VALUE_SERIALIZER', 'json')  # json, string, bytes
KAFKA_KEY_DESERIALIZER = os.getenv('KAFKA_KEY_DESERIALIZER', 'json')  # json, string, bytes
KAFKA_VALUE_DESERIALIZER = os.getenv('KAFKA_VALUE_DESERIALIZER', 'json')  # json, string, bytes


def get_kafka_producer_config() -> Dict[str, Any]:
    """
    Get Kafka producer configuration as a dictionary.
    
    Returns:
        dict: Kafka producer configuration parameters
    """
    config = {
        'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
        'acks': KAFKA_PRODUCER_ACKS,
        # 'retries': KAFKA_PRODUCER_RETRIES,
        # 'batch_size': KAFKA_PRODUCER_BATCH_SIZE,
        'linger_ms': KAFKA_PRODUCER_LINGER_MS,
        # 'buffer_memory': KAFKA_PRODUCER_BUFFER_MEMORY,
        # 'compression_type': KAFKA_PRODUCER_COMPRESSION_TYPE,
    }
    
    # Add security configuration if provided
    if KAFKA_SECURITY_PROTOCOL != 'PLAINTEXT':
        config['security_protocol'] = KAFKA_SECURITY_PROTOCOL
        
        if KAFKA_SECURITY_PROTOCOL in ['SASL_PLAINTEXT', 'SASL_SSL']:
            config['sasl_mechanism'] = KAFKA_SASL_MECHANISM
            if KAFKA_SASL_USERNAME:
                config['sasl_plain_username'] = KAFKA_SASL_USERNAME
            if KAFKA_SASL_PASSWORD:
                config['sasl_plain_password'] = KAFKA_SASL_PASSWORD
        
        if KAFKA_SECURITY_PROTOCOL in ['SSL', 'SASL_SSL']:
            if KAFKA_SSL_CA_LOCATION:
                config['ssl_cafile'] = KAFKA_SSL_CA_LOCATION
            if KAFKA_SSL_CERTIFICATE_LOCATION:
                config['ssl_certfile'] = KAFKA_SSL_CERTIFICATE_LOCATION
            if KAFKA_SSL_KEY_LOCATION:
                config['ssl_keyfile'] = KAFKA_SSL_KEY_LOCATION
    
    return config


def get_kafka_consumer_config(group_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Kafka consumer configuration as a dictionary.
    
    Args:
        group_id: Consumer group ID (overrides default if provided)
    
    Returns:
        dict: Kafka consumer configuration parameters
    """
    config = {
        'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
        'group_id': group_id or KAFKA_CONSUMER_GROUP_ID,
        'auto_offset_reset': KAFKA_CONSUMER_AUTO_OFFSET_RESET,
        'enable_auto_commit': KAFKA_CONSUMER_ENABLE_AUTO_COMMIT,
        'auto_commit_interval_ms': KAFKA_CONSUMER_AUTO_COMMIT_INTERVAL_MS,
        'session_timeout_ms': KAFKA_CONSUMER_SESSION_TIMEOUT_MS,
        'heartbeat_interval_ms': KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS,
        'max_poll_records': KAFKA_CONSUMER_MAX_POLL_RECORDS,
        'fetch_min_bytes': KAFKA_CONSUMER_FETCH_MIN_BYTES,
        'fetch_max_wait_ms': KAFKA_CONSUMER_FETCH_MAX_WAIT_MS,
    }
    
    # Add security configuration if provided
    if KAFKA_SECURITY_PROTOCOL != 'PLAINTEXT':
        config['security_protocol'] = KAFKA_SECURITY_PROTOCOL
        
        if KAFKA_SECURITY_PROTOCOL in ['SASL_PLAINTEXT', 'SASL_SSL']:
            config['sasl_mechanism'] = KAFKA_SASL_MECHANISM
            if KAFKA_SASL_USERNAME:
                config['sasl_plain_username'] = KAFKA_SASL_USERNAME
            if KAFKA_SASL_PASSWORD:
                config['sasl_plain_password'] = KAFKA_SASL_PASSWORD
        
        if KAFKA_SECURITY_PROTOCOL in ['SSL', 'SASL_SSL']:
            if KAFKA_SSL_CA_LOCATION:
                config['ssl_cafile'] = KAFKA_SSL_CA_LOCATION
            if KAFKA_SSL_CERTIFICATE_LOCATION:
                config['ssl_certfile'] = KAFKA_SSL_CERTIFICATE_LOCATION
            if KAFKA_SSL_KEY_LOCATION:
                config['ssl_keyfile'] = KAFKA_SSL_KEY_LOCATION
    
    return config


def get_kafka_listener_config() -> Dict[str, Any]:
    """
    Get Kafka listener configuration for event-driven consumption.
    
    Returns:
        dict: Kafka listener configuration parameters
    """
    return {
        'enabled': KAFKA_LISTENER_ENABLED,
        'topics': KAFKA_LISTENER_TOPICS,
        'group_id': KAFKA_LISTENER_GROUP_ID,
        'poll_timeout': KAFKA_LISTENER_POLL_TIMEOUT,
        'consumer_config': get_kafka_consumer_config(KAFKA_LISTENER_GROUP_ID)
    }
