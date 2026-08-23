import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import traceback

from .elastic_handler import ElasticHandler
from .elastic_config import get_elastic_config

logger = logging.getLogger(__name__)

# Global ElasticHandler instance
_elastic_handler: Optional[ElasticHandler] = None
_logging_enabled: bool = True

# Index configuration for request logs
REQUEST_LOG_INDEX_CONFIG = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "1s"
    },
    "mappings": {
        "properties": {
            "timestamp": {"type": "date"},
            "request_id": {"type": "keyword"},
            "method": {"type": "keyword"},
            "url": {"type": "keyword"},
            "path": {"type": "keyword"},
            "query_params": {"type": "object", "enabled": False},
            "headers": {"type": "object", "enabled": False},
            "user_id": {"type": "keyword"},
            "username": {"type": "keyword"},
            "user_permissions": {"type": "keyword"},
            "request_body": {"type": "object", "enabled": False},
            "response_status": {"type": "integer"},
            "response_body": {"type": "object", "enabled": False},
            "execution_time_ms": {"type": "float"},
            "ip_address": {"type": "ip"},
            "user_agent": {"type": "keyword"},
            "content_type": {"type": "keyword"},
            "content_length": {"type": "long"},
            "error_message": {"type": "text"},
            "error_traceback": {"type": "text"},
            "endpoint_name": {"type": "keyword"},
            "router_name": {"type": "keyword"},
            "tags": {"type": "keyword"}
        }
    }
}


def get_elastic_handler() -> ElasticHandler:
    """Get or create ElasticHandler instance"""
    global _elastic_handler
    if _elastic_handler is None:
        config = get_elastic_config()
        _elastic_handler = ElasticHandler(**config)
    return _elastic_handler


def enable_request_logging():
    """Enable request logging"""
    global _logging_enabled
    _logging_enabled = True


def disable_request_logging():
    """Disable request logging"""
    global _logging_enabled
    _logging_enabled = False


async def _log_request_to_elasticsearch(log_data: Dict[str, Any]) -> None:
    """Log request data to Elasticsearch"""
    if not _logging_enabled:
        return
    
    try:
        elastic_handler = get_elastic_handler()
        
        # Create index name with date pattern for better organization
        current_date = datetime.now().strftime("%Y-%m-%d")
        index_name = f"api-requests-{current_date}"
        
        # Ensure index exists
        await elastic_handler.ensure_index_exists(index_name, REQUEST_LOG_INDEX_CONFIG)
        
        # Index the log document
        await elastic_handler.index_document(index_name, log_data)
        
    except Exception as e:
        logger.error(f"Failed to log request to Elasticsearch: {e}")
        # Don't raise the exception to avoid breaking the API response


def _extract_user_info(request: Request) -> Dict[str, Any]:
    """Extract user information from request"""
    user_info = {
        "user_id": None,
        "username": None,
        "user_permissions": []
    }
    
    try:
        # Try to get user from request state (if set by auth middleware)
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_info["user_id"] = getattr(user, 'id', None)
            user_info["username"] = getattr(user, 'username', None)
            user_info["user_permissions"] = getattr(user, 'permissions', [])
    except Exception as e:
        logger.debug(f"Could not extract user info: {e}")
    
    return user_info


def _extract_request_data(request: Request) -> Dict[str, Any]:
    """Extract request data safely"""
    request_data = {
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "body": None,
        "content_type": request.headers.get("content-type", ""),
        "content_length": request.headers.get("content-length", 0)
    }
    
    # Remove sensitive headers
    sensitive_headers = ['authorization', 'cookie', 'x-api-key']
    for header in sensitive_headers:
        request_data["headers"].pop(header.lower(), None)
        request_data["headers"].pop(header, None)
    
    return request_data


def _extract_response_data(response: Response) -> Dict[str, Any]:
    """Extract response data safely"""
    response_data = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": None
    }
    
    # Remove sensitive headers
    sensitive_headers = ['set-cookie', 'authorization']
    for header in sensitive_headers:
        response_data["headers"].pop(header.lower(), None)
        response_data["headers"].pop(header, None)
    
    return response_data


def log_requests(
    index_name: str = "api-requests",
    include_request_body: bool = True,
    include_response_body: bool = True,
    include_headers: bool = True,
    include_query_params: bool = True,
    max_body_size: int = 10000,  # 10KB limit for body logging
    sensitive_fields: list = None
):
    """
    Decorator to log API requests to Elasticsearch
    
    Args:
        index_name: Custom index name for this endpoint
        include_request_body: Whether to include request body in logs
        include_response_body: Whether to include response body in logs
        include_headers: Whether to include headers in logs
        include_query_params: Whether to include query parameters in logs
        max_body_size: Maximum size of body to log (in bytes)
        sensitive_fields: List of sensitive field names to exclude from logging
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'key']
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            request = None
            response = None
            error_occurred = False
            error_message = None
            error_traceback = None
            
            # Find Request object in args or kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if not request:
                # If no request found, just call the function
                return await func(*args, **kwargs)
            
            # Extract initial request data
            request_data = _extract_request_data(request) if include_headers else {}
            user_info = _extract_user_info(request)
            
            # Extract request body if needed
            if include_request_body and request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.body()
                    if body and len(body) <= max_body_size:
                        try:
                            request_data["body"] = json.loads(body.decode('utf-8'))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            request_data["body"] = body.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.debug(f"Could not extract request body: {e}")
            
            # Filter sensitive data
            if request_data.get("body"):
                request_data["body"] = _filter_sensitive_data(
                    request_data["body"], sensitive_fields
                )
            
            try:
                # Execute the original function
                result = await func(*args, **kwargs)
                response = result if isinstance(result, Response) else None
                
                # Extract response data
                response_data = {}
                if response and include_response_body:
                    response_data = _extract_response_data(response)
                    
                    # Try to extract response body for JSONResponse
                    if isinstance(result, JSONResponse):
                        try:
                            response_data["body"] = result.body.decode('utf-8')
                            if response_data["body"]:
                                try:
                                    response_data["body"] = json.loads(response_data["body"])
                                except json.JSONDecodeError:
                                    pass
                        except Exception as e:
                            logger.debug(f"Could not extract response body: {e}")
                
                return result
                
            except Exception as e:
                error_occurred = True
                error_message = str(e)
                error_traceback = traceback.format_exc()
                raise
            
            finally:
                # Calculate execution time
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Prepare log data
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None),
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "execution_time_ms": round(execution_time, 2),
                    "endpoint_name": func.__name__,
                    "router_name": getattr(func, '__module__', '').split('.')[-1] if hasattr(func, '__module__') else None,
                    "tags": getattr(func, 'tags', []),
                    **user_info
                }
                
                # Add request data
                if include_headers:
                    log_data["headers"] = request_data.get("headers", {})
                if include_query_params:
                    log_data["query_params"] = request_data.get("query_params", {})
                if include_request_body and request_data.get("body"):
                    log_data["request_body"] = request_data["body"]
                
                # Add response data
                if response_data:
                    log_data["response_status"] = response_data.get("status_code")
                    if include_response_body and response_data.get("body"):
                        log_data["response_body"] = response_data["body"]
                
                # Add error information
                if error_occurred:
                    log_data["error_message"] = error_message
                    log_data["error_traceback"] = error_traceback
                
                # Log to Elasticsearch asynchronously (don't wait for it)
                asyncio.create_task(_log_request_to_elasticsearch(log_data))
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we'll just call them without logging
            # since we can't easily capture request/response data
            return func(*args, **kwargs)
        
        # Return async wrapper for async functions, sync wrapper for sync functions
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _filter_sensitive_data(data: Any, sensitive_fields: list) -> Any:
    """Filter out sensitive data from request/response bodies"""
    if isinstance(data, dict):
        filtered_data = {}
        for key, value in data.items():
            if any(sensitive_field.lower() in key.lower() for sensitive_field in sensitive_fields):
                filtered_data[key] = "***REDACTED***"
            else:
                filtered_data[key] = _filter_sensitive_data(value, sensitive_fields)
        return filtered_data
    elif isinstance(data, list):
        return [_filter_sensitive_data(item, sensitive_fields) for item in data]
    else:
        return data


# Convenience decorators for different logging levels
def log_minimal(func: Callable) -> Callable:
    """Log only basic request information"""
    return log_requests(
        include_request_body=False,
        include_response_body=False,
        include_headers=False,
        include_query_params=False
    )(func)


def log_standard(func: Callable) -> Callable:
    """Log standard request information (default)"""
    return log_requests()(func)


def log_detailed(func: Callable) -> Callable:
    """Log detailed request information including bodies"""
    return log_requests(
        include_request_body=True,
        include_response_body=True,
        include_headers=True,
        include_query_params=True,
        max_body_size=50000  # 50KB limit
    )(func)


def log_secure(func: Callable) -> Callable:
    """Log request information with enhanced security filtering"""
    return log_requests(
        include_request_body=True,
        include_response_body=True,
        include_headers=True,
        include_query_params=True,
        sensitive_fields=['password', 'token', 'secret', 'key', 'authorization', 'api_key', 'private_key']
    )(func)
