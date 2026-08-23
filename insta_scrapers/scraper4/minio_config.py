"""
MinIO configuration settings.
"""

import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

# MinIO Configuration
MINIO_ENDPOINT_URL = os.getenv('MINIO_ENDPOINT_URL', 'http://192.168.10.52:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_REGION = os.getenv('MINIO_REGION', 'us-east-1')
MINIO_TELEGRAM_CHANNEL_BUCKET_NAME = os.getenv('MINIO_TELEGRAM_CHANNEL_BUCKET_NAME', 'images')
MINIO_TELEGRAM_GROUP_BUCKET_NAME = os.getenv('MINIO_TELEGRAM_GROUP_BUCKET_NAME', 'images')
MINIO_TELEGRAM_USER_BUCKET_NAME = os.getenv('MINIO_TELEGRAM_USER_BUCKET_NAME', 'images')
MINIO_QUERIES_BUCKET_NAME = os.getenv('MINIO_QUERIES_BUCKET_NAME', 'images')

# URL expiration settings (in seconds)
DEFAULT_URL_EXPIRATION = int(os.getenv('MINIO_URL_EXPIRATION', '86400'))  # 24 hours
IMAGE_URL_EXPIRATION = int(os.getenv('MINIO_IMAGE_URL_EXPIRATION', '86400'))  # 24 hours
DOCUMENT_URL_EXPIRATION = int(os.getenv('MINIO_DOCUMENT_URL_EXPIRATION', '3600'))  # 1 hour


def get_minio_config(type: str = 'channel') -> dict:
    """
    Get MinIO configuration as a dictionary.
    
    Returns:
        dict: MinIO configuration parameters
    """
    config = {
        'endpoint_url': MINIO_ENDPOINT_URL,
        'access_key': MINIO_ACCESS_KEY,
        'secret_key': MINIO_SECRET_KEY,
        'region_name': MINIO_REGION,
        'bucket_name': MINIO_TELEGRAM_CHANNEL_BUCKET_NAME if type == 'channel' else MINIO_TELEGRAM_GROUP_BUCKET_NAME if type == 'group' else MINIO_TELEGRAM_USER_BUCKET_NAME if type == 'user' else MINIO_QUERIES_BUCKET_NAME if type == 'queries' else None
    } 
    cert_path = os.path.join('utils', 'minio_public.crt')
    if os.path.exists(cert_path):
        config['cert_file'] = cert_path
    return config
