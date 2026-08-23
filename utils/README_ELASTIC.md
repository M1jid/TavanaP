# Elasticsearch Handler

A comprehensive Python handler for managing Elasticsearch operations.

## Overview

The Elasticsearch handler provides a clean, consistent interface for interacting with Elasticsearch clusters. It includes functionality for:

- Creating and managing indices
- Indexing and searching documents
- Managing cluster health and status
- Querying documents by various criteria
- Bulk operations for high-performance indexing
- Monitoring Elasticsearch status
- Document CRUD operations

## Files Structure

```
utils/
├── elastic_handler.py      # Main handler class
├── elastic_config.py       # Configuration settings
├── elastic_integration.py  # FastAPI integration
├── elastic_example.py      # Usage examples
└── README_ELASTIC.md       # This documentation
```

## Installation

The handler requires the following dependencies:

```bash
pip install elasticsearch tenacity python-dotenv
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Elasticsearch Configuration
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_TIMEOUT=30
ELASTICSEARCH_MAX_RETRIES=5

# SSL Configuration
ELASTICSEARCH_VERIFY_CERTS=false
ELASTICSEARCH_SSL_SHOW_WARN=false

# Search and indexing settings
ELASTICSEARCH_DEFAULT_SEARCH_SIZE=10
ELASTICSEARCH_DEFAULT_BULK_SIZE=1000
ELASTICSEARCH_DEFAULT_REFRESH_INTERVAL=1s

# Index naming patterns
ELASTICSEARCH_INDEX_PREFIX=
ELASTICSEARCH_INDEX_SUFFIX=
```

### Configuration Functions

```python
from elastic_config import get_elastic_config, get_elastic_config_with_custom_timeout

# Get default configuration
config = get_elastic_config()

# Get configuration with custom timeout
config = get_elastic_config_with_custom_timeout(timeout=60)

# Get configuration with SSL settings
config = get_elastic_config_with_ssl(verify_certs=True, ssl_show_warn=True)
```

## Basic Usage

### Initialization

```python
from elastic_handler import ElasticHandler
from elastic_config import get_elastic_config

# Initialize with configuration
config = get_elastic_config()
elastic_handler = ElasticHandler(**config)

# Or initialize directly
elastic_handler = ElasticHandler(
    hosts="localhost:9200",
    username="elastic",
    password="changeme",
    timeout=30,
    max_retries=5
)
```

### Health Check

```python
# Check if Elasticsearch cluster is healthy
is_healthy = elastic_handler.health_check()
if is_healthy:
    print("Elasticsearch cluster is healthy!")
    
# Get cluster information
cluster_info = elastic_handler.get_cluster_info()
print(f"Cluster info: {cluster_info}")

# Get cluster health
health = elastic_handler.get_cluster_health()
print(f"Cluster health: {health}")
```

### Creating Indices

```python
# Create an index
index_name = "users"
index_config = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "user_id": {"type": "keyword"},
            "username": {"type": "text"},
            "email": {"type": "keyword"},
            "age": {"type": "integer"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}

success = elastic_handler.create_index(index_name, index_config)
if success:
    print(f"Index '{index_name}' created successfully!")
```

### Indexing Documents

```python
# Index a single document
user_data = {
    "user_id": "user123",
    "username": "john_doe",
    "email": "john@example.com",
    "age": 30,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

document_id = elastic_handler.index_document(index_name, user_data)
if document_id:
    print(f"Document indexed with ID: {document_id}")

# Bulk index multiple documents
users_data = [
    {"user_id": "user124", "username": "jane_smith", "email": "jane@example.com"},
    {"user_id": "user125", "username": "bob_wilson", "email": "bob@example.com"}
]

result = elastic_handler.bulk_index(index_name, users_data)
print(f"Bulk indexed {result['success_count']} documents")
```

### Searching Documents

```python
# Simple search
search_query = {
    "query": {
        "match": {
            "username": "john"
        }
    }
}

results = elastic_handler.search_documents(index_name, search_query)
if results:
    total_hits = results.get('hits', {}).get('total', {}).get('value', 0)
    hits = results.get('hits', {}).get('hits', [])
    print(f"Found {total_hits} documents")

# Complex search with filters
complex_query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"username": "john"}},
                {"range": {"age": {"gte": 18, "lte": 65}}}
            ],
            "filter": [
                {"term": {"is_active": True}}
            ]
        }
    },
    "sort": [{"created_at": {"order": "desc"}}]
}

results = elastic_handler.search_documents(index_name, complex_query, size=10)
```

### Document Operations

```python
# Get document by ID
document = elastic_handler.get_document_by_id(index_name, document_id)
if document:
    print(f"Retrieved document: {document}")

# Update document
update_data = {
    "age": 31,
    "updated_at": datetime.now().isoformat()
}

success = elastic_handler.update_document(index_name, document_id, update_data)
if success:
    print("Document updated successfully")

# Delete document
success = elastic_handler.delete_document(index_name, document_id)
if success:
    print("Document deleted successfully")
```

### Index Management

```python
# Check if index exists
exists = elastic_handler.index_exists(index_name)
print(f"Index exists: {exists}")

# Ensure index exists (create if it doesn't)
success = elastic_handler.ensure_index_exists(index_name, index_config)

# List all indices
indices = elastic_handler.list_indices()
print(f"All indices: {indices}")

# Get index count
count = elastic_handler.get_index_count(index_name)
print(f"Index has {count} documents")

# Get index status
status = elastic_handler.get_index_status(index_name)
print(f"Index status: {status}")

# Refresh index (make changes visible)
success = elastic_handler.refresh_index(index_name)

# Flush index (persist to disk)
success = elastic_handler.flush_index(index_name)

# Delete index
success = elastic_handler.delete_index(index_name)
```

## FastAPI Integration

The `elastic_integration.py` file provides FastAPI endpoints for all Elasticsearch operations.

### Setup

```python
from fastapi import FastAPI
from elastic_integration import router

app = FastAPI()
app.include_router(router)
```

### Available Endpoints

- `POST /elastic/create-index` - Create indices
- `DELETE /elastic/delete-index/{index_name}` - Delete indices
- `GET /elastic/index-exists/{index_name}` - Check if index exists
- `POST /elastic/ensure-index` - Ensure index exists
- `POST /elastic/index-document` - Index documents
- `POST /elastic/bulk-index` - Bulk index documents
- `GET /elastic/get-document/{index_name}/{document_id}` - Get document by ID
- `POST /elastic/search-documents` - Search documents
- `PUT /elastic/update-document` - Update documents
- `DELETE /elastic/delete-document/{index_name}/{document_id}` - Delete documents
- `GET /elastic/list-indices` - List all indices
- `GET /elastic/index-count/{index_name}` - Get document count
- `GET /elastic/index-status/{index_name}` - Get index status
- `GET /elastic/cluster-health` - Get cluster health
- `GET /elastic/cluster-info` - Get cluster info
- `GET /elastic/health` - Health check
- `POST /elastic/refresh-index/{index_name}` - Refresh index
- `POST /elastic/flush-index/{index_name}` - Flush index

### Example API Usage

```python
import requests

# Create an index
response = requests.post("http://localhost:8000/elastic/create-index", json={
    "index_name": "test_index",
    "body": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {"properties": {"id": {"type": "keyword"}}}
    }
})
print(response.json())

# Index a document
response = requests.post("http://localhost:8000/elastic/index-document", json={
    "index_name": "test_index",
    "document": {"id": "test123", "message": "Hello Elasticsearch!"}
})
print(response.json())

# Search documents
response = requests.post("http://localhost:8000/elastic/search-documents", json={
    "index_name": "test_index",
    "query": {"query": {"match": {"message": "Hello"}}}
})
print(response.json())
```

## Advanced Examples

### Logging System

```python
# Create logs index
logs_index = "application_logs"
logs_config = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
    "mappings": {
        "properties": {
            "timestamp": {"type": "date"},
            "level": {"type": "keyword"},
            "message": {"type": "text"},
            "service": {"type": "keyword"},
            "user_id": {"type": "keyword"}
        }
    }
}

elastic_handler.ensure_index_exists(logs_index, logs_config)

# Index log entries
log_entries = [
    {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": "User login successful",
        "service": "auth-service",
        "user_id": "user123"
    }
]

result = elastic_handler.bulk_index(logs_index, log_entries)

# Search for error logs
error_query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"level": "ERROR"}},
                {"range": {"timestamp": {"gte": "now-1h"}}}
            ]
        }
    }
}

error_results = elastic_handler.search_documents(logs_index, error_query)
```

### User Management

```python
# Create users index
users_index = "users"
users_config = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
    "mappings": {
        "properties": {
            "user_id": {"type": "keyword"},
            "username": {"type": "text"},
            "email": {"type": "keyword"},
            "age": {"type": "integer"},
            "is_active": {"type": "boolean"}
        }
    }
}

elastic_handler.ensure_index_exists(users_index, users_config)

# Search for active users
active_users_query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"is_active": True}},
                {"range": {"age": {"gte": 18, "lte": 65}}}
            ]
        }
    }
}

active_results = elastic_handler.search_documents(users_index, active_users_query)
```

### Error Handling

```python
try:
    # Initialize Elasticsearch handler
    config = get_elastic_config()
    elastic_handler = ElasticHandler(**config)
    
    # Health check
    if not elastic_handler.health_check():
        print("Elasticsearch cluster is not healthy")
        return
    
    # Create index
    success = elastic_handler.create_index("test_index", index_config)
    if not success:
        print("Failed to create index")
        return
        
    # Index document
    document_id = elastic_handler.index_document("test_index", data)
    if not document_id:
        print("Failed to index document")
        return
        
    print("Operation completed successfully!")
    
except Exception as e:
    print(f"Error: {str(e)}")
```

## Features

### Retry Mechanism

The handler includes automatic retry logic using the `tenacity` library:

- Exponential backoff with jitter
- Configurable retry attempts
- Retry only on specific exceptions (connection errors, timeouts)

### Connection Testing

The handler automatically tests the connection to Elasticsearch on initialization:

```python
# Connection is tested automatically
elastic_handler = ElasticHandler(**config)
# If connection fails, appropriate error messages are logged
```

### Comprehensive Logging

All operations are logged with appropriate levels:

- INFO: Successful operations
- ERROR: Failed operations
- DEBUG: Detailed operation information

### Type Safety

The handler uses Python type hints for better code quality and IDE support.

### Bulk Operations

Efficient bulk indexing for high-performance operations:

```python
# Bulk index with custom IDs
document_ids = ["doc1", "doc2", "doc3"]
result = elastic_handler.bulk_index(index_name, documents, document_ids)
```

## Best Practices

1. **Always check health before operations**: Use `health_check()` to ensure the cluster is available.

2. **Handle errors gracefully**: Wrap operations in try-catch blocks and handle failures appropriately.

3. **Use configuration files**: Store configuration in environment variables or configuration files.

4. **Monitor operations**: Use the logging functionality to monitor Elasticsearch operations.

5. **Use bulk operations**: For large datasets, use bulk indexing instead of individual document indexing.

6. **Refresh indices when needed**: Use `refresh_index()` to make recent changes visible in searches.

7. **Use appropriate mappings**: Define proper field mappings for better search performance.

8. **Monitor cluster health**: Regularly check cluster health and status.

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if Elasticsearch is running and accessible.
2. **Authentication errors**: Verify username and password configuration.
3. **Index already exists**: Use `check_exists=True` parameter to avoid errors.
4. **Mapping conflicts**: Ensure proper field mappings when creating indices.
5. **Timeout errors**: Increase timeout values in configuration.

### Debug Mode

Enable debug logging to get detailed information about operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Cluster Health Monitoring

```python
# Check cluster health
health = elastic_handler.get_cluster_health()
status = health.get('status', 'unknown')
if status == 'red':
    print("Cluster is in critical state")
elif status == 'yellow':
    print("Cluster has some issues")
elif status == 'green':
    print("Cluster is healthy")
```

## Contributing

When contributing to the Elasticsearch handler:

1. Follow the existing code structure and patterns
2. Add appropriate type hints
3. Include comprehensive error handling
4. Add logging for all operations
5. Update documentation for new features
6. Add tests for new functionality

## License

This Elasticsearch handler follows the same license as the parent project. 