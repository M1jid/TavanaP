# Request Logging System

A comprehensive request logging system for FastAPI applications that logs all API requests to Elasticsearch with detailed information including timing, user details, request/response data, and error tracking.

## Features

- **Automatic Request Logging**: Log all API requests with detailed information
- **Elasticsearch Integration**: Store logs in Elasticsearch for powerful querying and analytics
- **Flexible Configuration**: Choose from different logging levels (minimal, standard, detailed, secure)
- **Security**: Automatic filtering of sensitive data (passwords, tokens, etc.)
- **Performance Monitoring**: Track execution times and identify slow endpoints
- **Error Tracking**: Capture and log errors with full stack traces
- **User Context**: Log user information and permissions
- **Multiple Deployment Options**: Use decorators or middleware

## Installation

The system uses your existing Elasticsearch configuration from `elastic_config.py`. Make sure your Elasticsearch environment variables are set:

```bash
ELASTICSEARCH_HOSTS_READ=your_elasticsearch_host
ELASTICSEARCH_USERNAME=your_username
ELASTICSEARCH_PASSWORD=your_password
```

## Quick Start

### Option 1: Using Middleware (Recommended)

Add the middleware to your FastAPI application for automatic logging of all requests:

```python
from fastapi import FastAPI
from utils.request_logging_middleware import create_standard_logging_middleware

app = FastAPI()

# Add request logging middleware
app.add_middleware(create_standard_logging_middleware())
```

### Option 2: Using Decorators

Apply decorators to individual endpoints for selective logging:

```python
from fastapi import FastAPI
from utils.request_logger import log_standard, log_secure

app = FastAPI()

@app.get("/users")
@log_standard
async def get_users():
    return {"users": ["user1", "user2"]}

@app.post("/users")
@log_secure
async def create_user(request: Request):
    body = await request.json()
    return {"message": "User created"}
```

## Logging Levels

### 1. Minimal Logging (`log_minimal`)
- Basic request information only
- No request/response bodies
- No headers or query parameters
- Fastest performance

```python
@app.get("/health")
@log_minimal
async def health_check():
    return {"status": "healthy"}
```

### 2. Standard Logging (`log_standard`)
- Request method, URL, path
- User information
- Execution time
- Response status
- Basic headers and query parameters

```python
@app.get("/users")
@log_standard
async def get_users():
    return {"users": ["user1", "user2"]}
```

### 3. Detailed Logging (`log_detailed`)
- Everything from standard logging
- Request and response bodies (up to 50KB)
- Full headers and query parameters
- Most comprehensive logging

```python
@app.post("/users")
@log_detailed
async def create_user(request: Request):
    body = await request.json()
    return {"message": "User created"}
```

### 4. Secure Logging (`log_secure`)
- Everything from detailed logging
- Enhanced sensitive data filtering
- Additional security fields filtered out

```python
@app.post("/auth/login")
@log_secure
async def login(request: Request):
    body = await request.json()
    return {"token": "jwt_token"}
```

## Middleware Configuration

### Standard Middleware
```python
app.add_middleware(create_standard_logging_middleware())
```

### Detailed Middleware
```python
app.add_middleware(create_detailed_logging_middleware())
```

### Secure Middleware
```python
app.add_middleware(create_secure_logging_middleware())
```

### Custom Middleware
```python
app.add_middleware(create_request_logging_middleware(
    include_request_body=True,
    include_response_body=False,
    exclude_paths=['/health', '/metrics'],
    exclude_methods=['OPTIONS'],
    sensitive_fields=['password', 'token', 'ssn'],
    max_body_size=5000
))
```

## Logged Data Fields

Each log entry contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime | Request timestamp |
| `request_id` | string | Unique request identifier |
| `method` | string | HTTP method (GET, POST, etc.) |
| `url` | string | Full request URL |
| `path` | string | Request path |
| `query_params` | object | Query parameters |
| `headers` | object | Request headers (filtered) |
| `user_id` | string | User ID |
| `username` | string | Username |
| `user_permissions` | array | User permissions |
| `request_body` | object | Request body (if enabled) |
| `response_status` | integer | HTTP response status |
| `response_body` | object | Response body (if enabled) |
| `execution_time_ms` | float | Request execution time in milliseconds |
| `ip_address` | string | Client IP address |
| `user_agent` | string | User agent string |
| `content_type` | string | Request content type |
| `content_length` | long | Request content length |
| `error_message` | string | Error message (if error occurred) |
| `error_traceback` | string | Full error traceback |
| `endpoint_name` | string | Function/endpoint name |
| `router_name` | string | Router/module name |
| `tags` | array | Additional tags |

## Querying Logs

### Basic Queries

```python
from utils.elastic_handler import ElasticHandler
from utils.elastic_config import get_elastic_config
from datetime import datetime

# Initialize Elasticsearch handler
config = get_elastic_config()
elastic_handler = ElasticHandler(**config)

# Get today's index
today = datetime.now().strftime("%Y-%m-%d")
index_name = f"api-requests-{today}"

# Get all requests from today
query = {
    "query": {"match_all": {}},
    "sort": [{"timestamp": {"order": "desc"}}],
    "size": 100
}

result = await elastic_handler.search_documents(index_name, query)
```

### Advanced Queries

#### Get Slow Requests
```python
slow_requests_query = {
    "query": {
        "range": {
            "execution_time_ms": {"gt": 1000}
        }
    },
    "sort": [{"execution_time_ms": {"order": "desc"}}]
}
```

#### Get Requests with Errors
```python
error_requests_query = {
    "query": {
        "exists": {"field": "error_message"}
    },
    "sort": [{"timestamp": {"order": "desc"}}]
}
```

#### Get Requests by User
```python
user_requests_query = {
    "query": {
        "term": {"username": "admin"}
    },
    "sort": [{"timestamp": {"order": "desc"}}]
}
```

#### Get Requests by Endpoint
```python
endpoint_requests_query = {
    "query": {
        "term": {"endpoint_name": "get_users"}
    },
    "sort": [{"timestamp": {"order": "desc"}}]
}
```

#### Complex Queries
```python
complex_query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"method": "POST"}},
                {"term": {"username": "admin"}},
                {"exists": {"field": "error_message"}},
                {"range": {"execution_time_ms": {"gt": 500}}}
            ]
        }
    },
    "sort": [{"timestamp": {"order": "desc"}}]
}
```

## Analytics and Reporting

### Request Count by Method
```python
method_analytics_query = {
    "size": 0,
    "aggs": {
        "methods": {
            "terms": {
                "field": "method",
                "size": 10
            }
        }
    }
}
```

### Average Response Time by Endpoint
```python
response_time_analytics_query = {
    "size": 0,
    "aggs": {
        "endpoints": {
            "terms": {
                "field": "endpoint_name",
                "size": 20
            },
            "aggs": {
                "avg_response_time": {
                    "avg": {"field": "execution_time_ms"}
                }
            }
        }
    }
}
```

### Error Rate by Endpoint
```python
error_rate_analytics_query = {
    "size": 0,
    "aggs": {
        "endpoints": {
            "terms": {
                "field": "endpoint_name",
                "size": 20
            },
            "aggs": {
                "error_count": {
                    "filter": {
                        "exists": {"field": "error_message"}
                    }
                },
                "total_count": {
                    "value_count": {"field": "endpoint_name"}
                }
            }
        }
    }
}
```

## Configuration Options

### Decorator Options
```python
@log_requests(
    index_name="custom-api-requests",
    include_request_body=True,
    include_response_body=True,
    include_headers=True,
    include_query_params=True,
    max_body_size=10000,
    sensitive_fields=['password', 'token', 'secret']
)
```

### Middleware Options
```python
create_request_logging_middleware(
    include_request_body=True,
    include_response_body=True,
    include_headers=True,
    include_query_params=True,
    max_body_size=10000,
    sensitive_fields=['password', 'token', 'secret'],
    exclude_paths=['/health', '/metrics'],
    exclude_methods=['OPTIONS']
)
```

## Security Considerations

1. **Sensitive Data Filtering**: The system automatically filters out sensitive fields like passwords, tokens, and API keys
2. **Header Filtering**: Authorization headers and cookies are automatically removed
3. **Body Size Limits**: Large request/response bodies are truncated to prevent storage issues
4. **Error Handling**: Logging failures don't affect API responses

## Performance Considerations

1. **Asynchronous Logging**: All logging is done asynchronously to avoid blocking API responses
2. **Index Management**: Logs are organized by date for better performance and management
3. **Configurable Detail Levels**: Choose the right logging level for your needs
4. **Exclusion Options**: Exclude health checks and other high-frequency endpoints

## Troubleshooting

### Common Issues

1. **Elasticsearch Connection Errors**
   - Check your Elasticsearch configuration in `elastic_config.py`
   - Verify network connectivity to Elasticsearch
   - Check authentication credentials

2. **Missing Logs**
   - Verify logging is enabled: `enable_request_logging()`
   - Check if paths are excluded in middleware configuration
   - Verify Elasticsearch index exists and is writable

3. **Performance Issues**
   - Reduce logging detail level for high-traffic endpoints
   - Increase `max_body_size` limits if needed
   - Exclude health check and monitoring endpoints

### Debug Mode

Enable debug logging to see detailed information about the logging process:

```python
import logging
logging.getLogger('utils.request_logger').setLevel(logging.DEBUG)
```

## Examples

See `request_logging_example.py` for comprehensive examples of:
- Using different decorators
- Configuring middleware
- Querying logged data
- Running analytics
- Testing the system

## Integration with Your Application

The system has been integrated into your existing FastAPI application:

1. **Middleware Added**: Standard logging middleware is added to your main application
2. **Decorators Applied**: Your user routes have been updated with logging decorators
3. **Configuration**: Uses your existing Elasticsearch configuration

To customize the logging for your specific needs, you can:
- Modify the middleware configuration in `factory.py`
- Add/remove decorators from specific endpoints
- Adjust sensitive field filtering
- Change exclusion paths and methods
