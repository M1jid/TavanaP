import boto3
from botocore.client import Config
import os
from typing import Optional, BinaryIO, Union
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from datetime import datetime, timedelta
import mimetypes

logger = logging.getLogger(__name__)


class MinIOHandler:
    """
    MinIO handler class using boto3 to manage file operations with MinIO server.
    
    This class provides methods to:
    - Upload files to MinIO
    - Generate presigned URLs for file access
    - Check if files exist
    - Delete files
    - List files in a bucket
    """
    
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
        bucket_name: str = "images",
        cert_file: Optional[str] = None  # Add certificate file parameter
    ):
        """
        Initialize MinIO handler with connection parameters.
        
        Args:
            endpoint_url: MinIO server endpoint URL
            access_key: MinIO access key
            secret_key: MinIO secret key
            region_name: AWS region name (default: us-east-1)
            bucket_name: Default bucket name for operations
        """
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.bucket_name = bucket_name
        self.cert_file = cert_file

        # Initialize boto3 client
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            config=Config(signature_version='s3v4'),
            verify=True,
        )
        
        # Ensure bucket exists
        # self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> bool:
        """
        Ensure the default bucket exists, create if it doesn't.
        
        Returns:
            bool: True if bucket exists or was created successfully
        """
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' already exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket '{self.bucket_name}'")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket '{self.bucket_name}': {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket '{self.bucket_name}': {e}")
                return False
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return False
    
    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to MinIO.
        
        Args:
            file_path: Path to the file to upload
            object_name: Name to give the object in MinIO (default: filename)
            bucket_name: Bucket to upload to (default: self.bucket_name)
            content_type: Content type of the file (auto-detected if not provided)
            
        Returns:
            str: Object key if successful, None otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        bucket = bucket_name or self.bucket_name
        object_key = object_name or os.path.basename(file_path)
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'application/octet-stream'
        
        try:
            self.client.upload_file(
                file_path,
                bucket,
                object_key,
                ExtraArgs={'ContentType': content_type}
            )
            logger.info(f"Successfully uploaded {file_path} to {bucket}/{object_key}")
            return object_key
        except ClientError as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return None
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return None
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file object to MinIO.
        
        Args:
            file_obj: File-like object to upload
            object_name: Name to give the object in MinIO
            bucket_name: Bucket to upload to (default: self.bucket_name)
            content_type: Content type of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        bucket = bucket_name or self.bucket_name
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        try:
            self.client.upload_fileobj(file_obj, bucket, object_name, ExtraArgs=extra_args)
            logger.info(f"Successfully uploaded file object to {bucket}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file object to {bucket}/{object_name}: {e}")
            return False
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return False
    
    def generate_presigned_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expiration: int = 15*60,
        method: str = 'get_object'
    ) -> Optional[str]:
        """
        Generate a presigned URL for accessing a file.
        
        Args:
            object_name: Name of the object in MinIO
            bucket_name: Bucket containing the object (default: self.bucket_name)
            expiration: URL expiration time in seconds (default: 15 minutes)
            method: HTTP method for the presigned URL (default: 'get_object')
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """

        bucket = bucket_name or self.bucket_name
        try:
            return self.client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{object_name}: {e}")
            return None
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return None
    
    def file_exists(self, object_name: str, bucket_name: Optional[str] = None) -> bool:
        """
        Check if a file exists in MinIO.
        
        Args:
            object_name: Name of the object to check
            bucket_name: Bucket to check in (default: self.bucket_name)
            
        Returns:
            bool: True if file exists, False otherwise
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            self.client.head_object(Bucket=bucket, Key=object_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.error(f"Error checking if file exists {bucket}/{object_name}: {e}")
                return False
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return False
    
    def delete_file(self, object_name: str, bucket_name: Optional[str] = None) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            object_name: Name of the object to delete
            bucket_name: Bucket containing the object (default: self.bucket_name)
            
        Returns:
            bool: True if successful, False otherwise
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            self.client.delete_object(Bucket=bucket, Key=object_name)
            logger.info(f"Successfully deleted {bucket}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {bucket}/{object_name}: {e}")
            return False
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return False
    
    def list_files(
        self,
        prefix: str = "",
        bucket_name: Optional[str] = None,
        max_keys: int = 1000
    ) -> list:
        """
        List files in a bucket with optional prefix filter.
        
        Args:
            prefix: Prefix to filter files (default: "")
            bucket_name: Bucket to list files from (default: self.bucket_name)
            max_keys: Maximum number of keys to return (default: 1000)
            
        Returns:
            list: List of file keys
        """
        bucket = bucket_name or self.bucket_name
        files = []
        
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket,
                Prefix=prefix,
                PaginationConfig={'MaxItems': max_keys}
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
            
            logger.info(f"Listed {len(files)} files from {bucket} with prefix '{prefix}'")
            return files
        except ClientError as e:
            logger.error(f"Failed to list files from {bucket}: {e}")
            return []
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return []
    
    def get_file_info(self, object_name: str, bucket_name: Optional[str] = None) -> Optional[dict]:
        """
        Get information about a file in MinIO.
        
        Args:
            object_name: Name of the object
            bucket_name: Bucket containing the object (default: self.bucket_name)
            
        Returns:
            dict: File information including size, last_modified, content_type, etc.
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.head_object(Bucket=bucket, Key=object_name)
            return {
                'key': object_name,
                'bucket': bucket,
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            logger.error(f"Failed to get file info for {bucket}/{object_name}: {e}")
            return None
        except NoCredentialsError:
            logger.error("No credentials provided for MinIO")
            return None
    
    def create_image_url(
        self,
        image_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        expiration: int = 86400  # 24 hours default for images
    ) -> Optional[str]:
        """
        Convenience method to upload an image and return a presigned URL.
        
        Args:
            image_path: Path to the image file
            object_name: Name for the object in MinIO (default: filename with timestamp)
            expiration: URL expiration time in seconds (default: 24 hours)
            
        Returns:
            str: Presigned URL for the uploaded image, None if failed
        """
        # Generate object name with timestamp if not provided
        if not object_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            object_name = f"images/{name}_{timestamp}{ext}"
        
        # Upload the image
        uploaded_key = self.upload_file(image_path, object_name, bucket_name=bucket_name)
        if not uploaded_key:
            return None
        
        # Generate presigned URL
        return self.generate_presigned_url(uploaded_key, expiration=expiration, bucket_name=bucket_name)
