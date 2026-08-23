"""
Example usage of the request logging system

This script demonstrates how to:
1. Use different logging decorators
2. Configure middleware
3. Query logged data from Elasticsearch
"""

import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from .request_logger import (
    log_requests, 
    log_minimal, 
    log_standard, 
    log_detailed, 
    log_secure,
    enable_request_logging,
    disable_request_logging
)
from .request_logging_middleware import (
    create_request_logging_middleware,
    create_minimal_logging_middleware,
    create_standard_logging_middleware,
    create_detailed_logging_middleware,
    create_secure_logging_middleware
)
from .elastic_handler import ElasticHandler
from .elastic_config import get_elastic_config


# Example 1: Using decorators on individual endpoints
app = FastAPI()

@app.get("/users")
@log_standard  # Standard logging
async def get_users():
    return {"users": ["user1", "user2", "user3"]}

@app.post("/users")
@log_secure  # Secure logging with sensitive data filtering
async def create_user(request: Request):
    body = await request.json()
    return {"message": "User created", "user_id": 123}

@app.get("/health")
@log_minimal  # Minimal logging
async def health_check():
    return {"status": "healthy"}

@app.put("/users/{user_id}")
@log_requests(
    include_request_body=True,
    include_response_body=True,
    max_body_size=5000,
    sensitive_fields=['password', 'ssn', 'credit_card']
)
async def update_user(user_id: int, request: Request):
    body = await request.json()
    return {"message": f"User {user_id} updated"}


# Example 2: Using middleware for automatic logging
app_with_middleware = FastAPI()

# Add different types of middleware
app_with_middleware.add_middleware(create_standard_logging_middleware())

# Or for more detailed logging:
# app_with_middleware.add_middleware(create_detailed_logging_middleware())

# Or for secure logging:
# app_with_middleware.add_middleware(create_secure_logging_middleware())

# Or custom configuration:
# app_with_middleware.add_middleware(create_request_logging_middleware(
#     include_request_body=True,
#     include_response_body=False,
#     exclude_paths=['/health', '/metrics'],
#     exclude_methods=['OPTIONS'],
#     sensitive_fields=['password', 'token']
# ))


@app_with_middleware.get("/api/users")
async def get_users_middleware():
    return {"users": ["user1", "user2"]}

@app_with_middleware.post("/api/users")
async def create_user_middleware(request: Request):
    body = await request.json()
    return {"message": "User created"}


# Example 3: Querying logged data from Elasticsearch
async def query_request_logs():
    """Example of how to query request logs from Elasticsearch"""
    
    # Initialize Elasticsearch handler
    config = get_elastic_config()
    elastic_handler = ElasticHandler(**config)
    
    # Get today's index name
    today = datetime.now().strftime("%Y-%m-%d")
    index_name = f"api-requests-{today}"
    
    # Example queries
    
    # 1. Get all requests from today
    all_requests_query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "size": 100
    }
    
    # 2. Get requests with errors
    error_requests_query = {
        "query": {
            "exists": {
                "field": "error_message"
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 3. Get slow requests (execution time > 1000ms)
    slow_requests_query = {
        "query": {
            "range": {
                "execution_time_ms": {
                    "gt": 1000
                }
            }
        },
        "sort": [
            {"execution_time_ms": {"order": "desc"}}
        ]
    }
    
    # 4. Get requests by specific user
    user_requests_query = {
        "query": {
            "term": {
                "username": "admin"
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 5. Get requests by endpoint
    endpoint_requests_query = {
        "query": {
            "term": {
                "endpoint_name": "get_users"
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 6. Get requests by HTTP method
    method_requests_query = {
        "query": {
            "term": {
                "method": "POST"
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 7. Get requests within time range
    time_range_query = {
        "query": {
            "range": {
                "timestamp": {
                    "gte": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "lte": datetime.now().isoformat()
                }
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 8. Get requests with specific status codes
    status_requests_query = {
        "query": {
            "terms": {
                "response_status": [400, 401, 403, 404, 500]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 9. Get requests by IP address
    ip_requests_query = {
        "query": {
            "term": {
                "ip_address": "192.168.1.100"
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    # 10. Complex query: Get slow POST requests with errors from specific user
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
        "sort": [
            {"timestamp": {"order": "desc"}}
        ]
    }
    
    try:
        # Execute one of the queries
        result = await elastic_handler.search_documents(
            index_name=index_name,
            query=all_requests_query,
            size=50
        )
        
        if result:
            hits = result.get('hits', {}).get('hits', [])
            print(f"Found {len(hits)} requests")
            
            for hit in hits:
                source = hit.get('_source', {})
                print(f"Timestamp: {source.get('timestamp')}")
                print(f"Method: {source.get('method')}")
                print(f"Path: {source.get('path')}")
                print(f"User: {source.get('username')}")
                print(f"Execution Time: {source.get('execution_time_ms')}ms")
                print(f"Status: {source.get('response_status')}")
                if source.get('error_message'):
                    print(f"Error: {source.get('error_message')}")
                print("-" * 50)
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")


# Example 4: Analytics and reporting functions
async def get_request_analytics():
    """Get analytics about API requests"""
    
    config = get_elastic_config()
    elastic_handler = ElasticHandler(**config)
    
    today = datetime.now().strftime("%Y-%m-%d")
    index_name = f"api-requests-{today}"
    
    # 1. Request count by method
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
    
    # 2. Average response time by endpoint
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
                        "avg": {
                            "field": "execution_time_ms"
                        }
                    }
                }
            }
        }
    }
    
    # 3. Error rate by endpoint
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
                            "exists": {
                                "field": "error_message"
                            }
                        }
                    },
                    "total_count": {
                        "value_count": {
                            "field": "endpoint_name"
                        }
                    }
                }
            }
        }
    }
    
    # 4. Requests per hour
    hourly_analytics_query = {
        "size": 0,
        "aggs": {
            "requests_per_hour": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": "hour"
                }
            }
        }
    }
    
    try:
        # Execute analytics queries
        method_result = await elastic_handler.search_documents(
            index_name=index_name,
            query=method_analytics_query
        )
        
        if method_result:
            methods = method_result.get('aggregations', {}).get('methods', {}).get('buckets', [])
            print("Requests by method:")
            for method in methods:
                print(f"  {method['key']}: {method['doc_count']}")
        
    except Exception as e:
        print(f"Error getting analytics: {e}")


# Example 5: Testing the logging system
def test_logging_system():
    """Test the logging system with sample requests"""
    
    client = TestClient(app)
    
    # Test different endpoints
    print("Testing logging system...")
    
    # Test GET request
    response = client.get("/users")
    print(f"GET /users - Status: {response.status_code}")
    
    # Test POST request with sensitive data
    response = client.post("/users", json={
        "username": "testuser",
        "password": "secretpassword",
        "email": "test@example.com"
    })
    print(f"POST /users - Status: {response.status_code}")
    
    # Test PUT request
    response = client.put("/users/123", json={
        "username": "updateduser",
        "ssn": "123-45-6789"
    })
    print(f"PUT /users/123 - Status: {response.status_code}")
    
    # Test health check
    response = client.get("/health")
    print(f"GET /health - Status: {response.status_code}")


if __name__ == "__main__":
    # Test the logging system
    test_logging_system()
    
    # Query logs (uncomment to run)
    # asyncio.run(query_request_logs())
    
    # Get analytics (uncomment to run)
    # asyncio.run(get_request_analytics())
