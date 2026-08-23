"""
Example usage of the MinIOHandler class.
"""

from minio_handler import MinIOHandler
from minio_config import get_minio_config
import os


def example_usage():
    """Example of how to use the MinIOHandler class."""
    
    # Initialize MinIO handler with configuration
    config = get_minio_config()
    minio_handler = MinIOHandler(**config)
    
    # Example 1: Upload an image and get a presigned URL
    image_path = "/path/to/your/image.jpg"
    if os.path.exists(image_path):
        # Upload image and get presigned URL
        image_url = minio_handler.create_image_url(image_path)
        if image_url:
            print(f"Image uploaded successfully! URL: {image_url}")
        else:
            print("Failed to upload image")
    
    # Example 2: Upload a file with custom name
    file_path = "/path/to/your/document.pdf"
    if os.path.exists(file_path):
        object_name = "documents/my_document.pdf"
        uploaded_key = minio_handler.upload_file(file_path, object_name)
        if uploaded_key:
            # Generate presigned URL for the uploaded file
            file_url = minio_handler.generate_presigned_url(uploaded_key, expiration=3600)
            print(f"File uploaded successfully! URL: {file_url}")
        else:
            print("Failed to upload file")
    
    # Example 3: Check if a file exists
    object_name = "images/example.jpg"
    if minio_handler.file_exists(object_name):
        print(f"File {object_name} exists")
        # Get file information
        file_info = minio_handler.get_file_info(object_name)
        if file_info:
            print(f"File size: {file_info['size']} bytes")
            print(f"Content type: {file_info['content_type']}")
    else:
        print(f"File {object_name} does not exist")
    
    # Example 4: List files in a bucket
    files = minio_handler.list_files(prefix="images/", max_keys=10)
    print(f"Found {len(files)} files with prefix 'images/':")
    for file_key in files:
        print(f"  - {file_key}")
    
    # Example 5: Delete a file
    object_to_delete = "images/old_image.jpg"
    if minio_handler.delete_file(object_to_delete):
        print(f"Successfully deleted {object_to_delete}")
    else:
        print(f"Failed to delete {object_to_delete}")


def example_with_error_handling():
    """Example with proper error handling."""
    
    try:
        # Initialize MinIO handler
        config = get_minio_config()
        minio_handler = MinIOHandler(**config)
        
        # Upload image and get URL
        image_path = "/path/to/image.jpg"
        image_url = minio_handler.create_image_url(image_path)
        
        if image_url:
            return {
                "success": True,
                "url": image_url,
                "message": "Image uploaded successfully"
            }
        else:
            return {
                "success": False,
                "url": None,
                "message": "Failed to upload image"
            }
            
    except Exception as e:
        return {
            "success": False,
            "url": None,
            "message": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    print("MinIO Handler Example Usage")
    print("=" * 40)
    
    # Run examples
    example_usage()
    
    print("\n" + "=" * 40)
    print("Error handling example:")
    result = example_with_error_handling()
    print(f"Result: {result}") 
