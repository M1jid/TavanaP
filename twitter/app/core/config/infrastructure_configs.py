"""
Infrastructure configuration definitions for the Telegram application.

This module contains configuration for:
- MinIO
- Redis
- PostgreSQL
- Proxy settings
"""

from app.core.config import settings

# Infrastructure Configuration
INFRASTRUCTURE_CONFIGS = {
    "minio": {
        "endpoint": settings.MINIO_ENDPOINT,
        "access_key": settings.MINIO_ACCESS_KEY,
        "secret_key": settings.MINIO_SECRET_KEY,
        "secure": settings.MINIO_SECURE,
        "bucket_name": settings.MINIO_BUCKET_NAME,
    },
    "redis": {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "db": settings.REDIS_DB,
    },
    "postgresql": {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
        "database": settings.POSTGRES_DB,
    },
    "proxy": {
        "protocol": settings.PROXY_PROTOCOL,
        "host": settings.PROXY_HOST,
        "port": settings.PROXY_PORT,
    }
}

__all__ = ["INFRASTRUCTURE_CONFIGS"]
