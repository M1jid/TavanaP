"""
Configuration module for the Telegram application.

This module contains all configuration definitions for:
- Kafka streams and connectors
- Elasticsearch indices
- Infrastructure components (MinIO, Redis, PostgreSQL)
"""

from .kafka_configs import KAFKA_STREAM_DEFINITIONS, KAFKA_CONNECTOR_DEFINITIONS
from .elasticsearch_configs import ELASTICSEARCH_INDEX_DEFINITIONS
from .infrastructure_configs import INFRASTRUCTURE_CONFIGS

__all__ = [
    "KAFKA_STREAM_DEFINITIONS",
    "KAFKA_CONNECTOR_DEFINITIONS", 
    "ELASTICSEARCH_INDEX_DEFINITIONS",
    "INFRASTRUCTURE_CONFIGS"
]
