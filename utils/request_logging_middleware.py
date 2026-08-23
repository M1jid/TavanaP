import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import traceback

from .request_logger import get_elastic_handler, REQUEST_LOG_INDEX_CONFIG, _filter_sensitive_data

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    FastAPI middleware to automatically log all requests to Elasticsearch
    """
    
    def __init__(
        self,
        include_request_body: bool = True,
        include_response_body: bool = True,
        include_headers: bool = True,
        include_query_params: bool = True,
        max_body_size: int = 10000,
        sensitive_fields: list = None,
        exclude_paths: list = None,
        exclude_methods: list = None
    ):
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
        self.include_headers = include_headers
        self.include_query_params = include_query_params
        self.max_body_size = max_body_size
        self.sensitive_fields = sensitive_fields or ['password', 'token', 'secret', 'key']
        self.exclude_paths = exclude_paths or ['/docs', '/redoc', '/openapi.json', '/status']
        self.exclude_methods = exclude_methods or ['OPTIONS']
    
    async def __call__(self, request: Request, call_next):
        # Skip logging for excluded paths and methods
        if (request.url.path in self.exclude_paths or 
            request.method in self.exclude_methods):
            return await call_next(request)
        
        start_time = time.time()
        error_occurred = False
        error_message = None
        error_traceback = None
        
        # Extract request data
        request_data = self._extract_request_data(request)
        user_info = self._extract_user_info(request)
        
        # Extract request body if needed
        if self.include_request_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body and len(body) <= self.max_body_size:
                    try:
                        request_data["body"] = json.loads(body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_data["body"] = body.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.debug(f"Could not extract request body: {e}")
        
        # Filter sensitive data
        if request_data.get("body"):
            request_data["body"] = _filter_sensitive_data(
                request_data["body"], self.sensitive_fields
            )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Extract response data
            response_data = {}
            if self.include_response_body:
                response_data = self._extract_response_data(response)
                
                # Try to extract response body for JSONResponse
                if isinstance(response, JSONResponse):
                    try:
                        response_data["body"] = response.body.decode('utf-8')
                        if response_data["body"]:
                            try:
                                response_data["body"] = json.loads(response_data["body"])
                            except json.JSONDecodeError:
                                pass
                    except Exception as e:
                        logger.debug(f"Could not extract response body: {e}")
            
            return response
            
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
                "endpoint_name": "middleware_captured",
                "router_name": "middleware",
                "tags": ["middleware_logged"],
                **user_info
            }
            
            # Add request data
            if self.include_headers:
                log_data["headers"] = request_data.get("headers", {})
            if self.include_query_params:
                log_data["query_params"] = request_data.get("query_params", {})
            if self.include_request_body and request_data.get("body"):
                log_data["request_body"] = request_data["body"]
            
            # Add response data
            if response_data:
                log_data["response_status"] = response_data.get("status_code")
                if self.include_response_body and response_data.get("body"):
                    log_data["response_body"] = response_data["body"]
            
            # Add error information
            if error_occurred:
                log_data["error_message"] = error_message
                log_data["error_traceback"] = error_traceback
            
            # Log to Elasticsearch asynchronously (don't wait for it)
            asyncio.create_task(self._log_request_to_elasticsearch(log_data))
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
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
    
    def _extract_request_data(self, request: Request) -> Dict[str, Any]:
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
    
    def _extract_response_data(self, response: Response) -> Dict[str, Any]:
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
    
    async def _log_request_to_elasticsearch(self, log_data: Dict[str, Any]) -> None:
        """Log request data to Elasticsearch"""
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


# Convenience function to create middleware with different configurations
def create_request_logging_middleware(
    include_request_body: bool = True,
    include_response_body: bool = True,
    include_headers: bool = True,
    include_query_params: bool = True,
    max_body_size: int = 10000,
    sensitive_fields: list = None,
    exclude_paths: list = None,
    exclude_methods: list = None
) -> RequestLoggingMiddleware:
    """
    Create a request logging middleware with specified configuration
    
    Args:
        include_request_body: Whether to include request body in logs
        include_response_body: Whether to include response body in logs
        include_headers: Whether to include headers in logs
        include_query_params: Whether to include query parameters in logs
        max_body_size: Maximum size of body to log (in bytes)
        sensitive_fields: List of sensitive field names to exclude from logging
        exclude_paths: List of paths to exclude from logging
        exclude_methods: List of HTTP methods to exclude from logging
    
    Returns:
        RequestLoggingMiddleware: Configured middleware instance
    """
    return RequestLoggingMiddleware(
        include_request_body=include_request_body,
        include_response_body=include_response_body,
        include_headers=include_headers,
        include_query_params=include_query_params,
        max_body_size=max_body_size,
        sensitive_fields=sensitive_fields,
        exclude_paths=exclude_paths,
        exclude_methods=exclude_methods
    )


# Pre-configured middleware instances
def create_minimal_logging_middleware() -> RequestLoggingMiddleware:
    """Create middleware that logs only basic request information"""
    return create_request_logging_middleware(
        include_request_body=False,
        include_response_body=False,
        include_headers=False,
        include_query_params=False
    )


def create_standard_logging_middleware() -> RequestLoggingMiddleware:
    """Create middleware that logs standard request information"""
    return create_request_logging_middleware()


def create_detailed_logging_middleware() -> RequestLoggingMiddleware:
    """Create middleware that logs detailed request information"""
    return create_request_logging_middleware(
        include_request_body=True,
        include_response_body=True,
        include_headers=True,
        include_query_params=True,
        max_body_size=50000
    )


def create_secure_logging_middleware() -> RequestLoggingMiddleware:
    """Create middleware with enhanced security filtering"""
    return create_request_logging_middleware(
        include_request_body=True,
        include_response_body=True,
        include_headers=True,
        include_query_params=True,
        sensitive_fields=['password', 'token', 'secret', 'key', 'authorization', 'api_key', 'private_key']
    )
