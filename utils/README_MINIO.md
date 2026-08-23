# MinIO Handler

A comprehensive MinIO client handler using boto3 for managing file operations with MinIO server.

## 🚀 Features

- **File Upload**: Upload files and file objects to MinIO
- **Presigned URLs**: Generate secure, time-limited URLs for file access
- **File Management**: Check existence, delete files, list files
- **Image Handling**: Specialized methods for image upload and URL generation
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Environment-based configuration management

## 📦 Installation

Make sure you have the required dependencies:

```bash
pip install boto3
```

## ⚙️ Configuration

Set up your environment variables in `.env` file:

```env
MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_REGION=us-east-1
MINIO_BUCKET_NAME=images
MINIO_URL_EXPIRATION=86400
MINIO_IMAGE_URL_EXPIRATION=86400
MINIO_DOCUMENT_URL_EXPIRATION=3600
```

## 🔧 Basic Usage

### Initialize MinIO Handler

```python
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config

# Using configuration
config = get_minio_config()
minio_handler = MinIOHandler(**config)

# Or direct initialization
minio_handler = MinIOHandler(
    endpoint_url="http://localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    bucket_name="images"
)
```

### Upload Image and Get URL

```python
# Upload image and get presigned URL
image_path = "/path/to/image.jpg"
image_url = minio_handler.create_image_url(image_path)

if image_url:
    print(f"Image URL: {image_url}")
else:
    print("Upload failed")
```

### Upload File with Custom Name

```python
# Upload file with custom object name
file_path = "/path/to/document.pdf"
object_name = "documents/my_document.pdf"
uploaded_key = minio_handler.upload_file(file_path, object_name)

if uploaded_key:
    # Generate presigned URL
    file_url = minio_handler.generate_presigned_url(uploaded_key, expiration=3600)
    print(f"File URL: {file_url}")
```

### Check File Existence

```python
object_name = "images/example.jpg"
if minio_handler.file_exists(object_name):
    print("File exists")
    # Get file information
    file_info = minio_handler.get_file_info(object_name)
    print(f"File size: {file_info['size']} bytes")
```

### List Files

```python
# List files with prefix
files = minio_handler.list_files(prefix="images/", max_keys=10)
for file_key in files:
    print(f"File: {file_key}")
```

### Delete File

```python
object_name = "images/old_image.jpg"
if minio_handler.delete_file(object_name):
    print("File deleted successfully")
```

## 🌐 FastAPI Integration

### Include MinIO Router

```python
from fastapi import FastAPI
from utils.minio_integration import router as minio_router

app = FastAPI()
app.include_router(minio_router)
```

### Available Endpoints

- `POST /minio/upload-image` - Upload image file
- `GET /minio/image-url/{object_name}` - Get presigned URL for image
- `DELETE /minio/delete-image/{object_name}` - Delete image
- `GET /minio/list-images` - List images in bucket
- `GET /minio/image-info/{object_name}` - Get image information

### Example Upload Request

```bash
curl -X POST "http://localhost:8000/minio/upload-image" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg"
```

## 🔗 Integration with Telegram Endpoints

### Update Channel Image Endpoint

```python
from utils.minio_integration import get_channel_image_url, upload_channel_image

@router.get("/channels/image")
async def get_channel_image(channel_id: int):
    """Get channel profile image"""
    image_url = await get_channel_image_url(channel_id)
    
    if image_url:
        return {"image_url": image_url}
    else:
        raise HTTPException(status_code=404, detail="Channel image not found")
```

### Upload Channel Image

```python
@router.post("/channels/upload-image")
async def upload_channel_image_endpoint(
    channel_id: int,
    file: UploadFile = File(...)
):
    """Upload channel profile image"""
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        try:
            image_url = upload_channel_image(channel_id, temp_file.name)
            if image_url:
                return {"image_url": image_url}
            else:
                raise HTTPException(status_code=500, detail="Upload failed")
        finally:
            os.unlink(temp_file.name)
```

## 📋 API Reference

### MinIOHandler Class

#### Methods

- `__init__(endpoint_url, access_key, secret_key, region_name, bucket_name)` - Initialize handler
- `upload_file(file_path, object_name, bucket_name, content_type)` - Upload file
- `upload_fileobj(file_obj, object_name, bucket_name, content_type)` - Upload file object
- `generate_presigned_url(object_name, bucket_name, expiration, method)` - Generate presigned URL
- `file_exists(object_name, bucket_name)` - Check if file exists
- `delete_file(object_name, bucket_name)` - Delete file
- `list_files(prefix, bucket_name, max_keys)` - List files
- `get_file_info(object_name, bucket_name)` - Get file information
- `create_image_url(image_path, object_name, expiration)` - Upload image and get URL

## 🛠️ Error Handling

The handler includes comprehensive error handling:

```python
try:
    image_url = minio_handler.create_image_url(image_path)
    if image_url:
        return {"success": True, "url": image_url}
    else:
        return {"success": False, "error": "Upload failed"}
except Exception as e:
    return {"success": False, "error": str(e)}
```

## 🔒 Security

- **Presigned URLs**: Time-limited access to files
- **Environment Variables**: Secure configuration management
- **Content Type Validation**: Ensures proper file types
- **Error Logging**: Comprehensive logging for debugging

## 📝 Examples

See `minio_example.py` for complete usage examples and `minio_integration.py` for FastAPI integration examples.

## 🚀 Getting Started

1. Set up your MinIO server
2. Configure environment variables
3. Initialize the MinIO handler
4. Start uploading and managing files!

```python
# Quick start
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config

config = get_minio_config()
minio = MinIOHandler(**config)

# Upload image
url = minio.create_image_url("/path/to/image.jpg")
print(f"Image URL: {url}")
``` 