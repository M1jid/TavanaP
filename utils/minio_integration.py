"""
Integration example for using MinIOHandler in FastAPI endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os
import tempfile

from minio_handler import MinIOHandler
from minio_config import get_minio_config

# Initialize MinIO handler
minio_config = get_minio_config()
minio_handler = MinIOHandler(**minio_config)

router = APIRouter(prefix="/minio", tags=["MinIO Operations"])


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    object_name: Optional[str] = None,
    expiration: int = 86400
):
    """
    Upload an image file to MinIO and return a presigned URL.
    
    Args:
        file: The image file to upload
        object_name: Optional custom name for the object
        expiration: URL expiration time in seconds (default: 24 hours)
    
    Returns:
        JSON response with upload status and URL
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        # Write uploaded file to temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        try:
            # Upload to MinIO and get presigned URL
            image_url = minio_handler.create_image_url(
                temp_file.name,
                object_name=object_name,
                expiration=expiration
            )
            
            if image_url:
                return JSONResponse({
                    "success": True,
                    "url": image_url,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content)
                })
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to upload image to MinIO"
                )
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file.name)


@router.get("/image-url/{object_name}")
async def get_image_url(
    object_name: str,
    expiration: int = 86400
):
    """
    Generate a presigned URL for an existing image in MinIO.
    
    Args:
        object_name: Name of the object in MinIO
        expiration: URL expiration time in seconds (default: 24 hours)
    
    Returns:
        JSON response with the presigned URL
    """
    # Check if file exists
    if not minio_handler.file_exists(object_name):
        raise HTTPException(
            status_code=404,
            detail=f"Image '{object_name}' not found"
        )
    
    # Generate presigned URL
    image_url = minio_handler.generate_presigned_url(
        object_name,
        expiration=expiration
    )
    
    if image_url:
        return JSONResponse({
            "success": True,
            "url": image_url,
            "object_name": object_name,
            "expiration_seconds": expiration
        })
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned URL"
        )


@router.delete("/delete-image/{object_name}")
async def delete_image(object_name: str):
    """
    Delete an image from MinIO.
    
    Args:
        object_name: Name of the object to delete
    
    Returns:
        JSON response with deletion status
    """
    # Check if file exists
    if not minio_handler.file_exists(object_name):
        raise HTTPException(
            status_code=404,
            detail=f"Image '{object_name}' not found"
        )
    
    # Delete file
    if minio_handler.delete_file(object_name):
        return JSONResponse({
            "success": True,
            "message": f"Image '{object_name}' deleted successfully"
        })
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete image"
        )


@router.get("/list-images")
async def list_images(
    prefix: str = "images/",
    max_keys: int = 100
):
    """
    List images in MinIO bucket.
    
    Args:
        prefix: Prefix to filter images (default: "images/")
        max_keys: Maximum number of keys to return (default: 100)
    
    Returns:
        JSON response with list of image keys
    """
    files = minio_handler.list_files(prefix=prefix, max_keys=max_keys)
    
    return JSONResponse({
        "success": True,
        "files": files,
        "count": len(files),
        "prefix": prefix
    })


@router.get("/image-info/{object_name}")
async def get_image_info(object_name: str):
    """
    Get information about an image in MinIO.
    
    Args:
        object_name: Name of the object
    
    Returns:
        JSON response with image information
    """
    # Check if file exists
    if not minio_handler.file_exists(object_name):
        raise HTTPException(
            status_code=404,
            detail=f"Image '{object_name}' not found"
        )
    
    # Get file information
    file_info = minio_handler.get_file_info(object_name)
    
    if file_info:
        return JSONResponse({
            "success": True,
            "info": file_info
        })
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to get image information"
        )


# Example of how to integrate with your existing telegram endpoints
def get_channel_image_url(channel_id: int) -> Optional[str]:
    """
    Example function to get channel image URL from MinIO.
    This could be integrated into your telegram channels endpoint.
    
    Args:
        channel_id: Telegram channel ID
    
    Returns:
        Presigned URL for the channel image, or None if not found
    """
    object_name = f"channels/{channel_id}/profile.jpg"
    
    if minio_handler.file_exists(object_name):
        return minio_handler.generate_presigned_url(object_name)
    
    return None


def upload_channel_image(channel_id: int, image_path: str) -> Optional[str]:
    """
    Example function to upload channel image to MinIO.
    
    Args:
        channel_id: Telegram channel ID
        image_path: Path to the image file
    
    Returns:
        Presigned URL for the uploaded image, or None if failed
    """
    object_name = f"channels/{channel_id}/profile.jpg"
    
    return minio_handler.create_image_url(image_path, object_name) 
