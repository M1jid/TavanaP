# ksqlDB Handler

A comprehensive Python handler for managing ksqlDB operations.

## Overview

The ksqlDB handler provides a clean, consistent interface for interacting with ksqlDB servers. It includes functionality for:

- Executing ksqlDB queries with retry mechanisms
- Creating and managing streams and tables
- Creating and managing sink connectors
- Inserting data into streams
- Listing and describing ksqlDB objects
- Dropping streams, tables, and connectors
- Health checks and server monitoring

## Files Structure

```
utils/
├── ksqldb_handler.py      # Main handler class
├── ksqldb_config.py       # Configuration settings
├── ksqldb_integration.py  # FastAPI integration
├── ksqldb_example.py      # Usage examples
└── README_KSQLDB.md       # This documentation
```

## Installation

The handler requires the following dependencies:

```bash
pip install requests tenacity python-dotenv
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# ksqlDB Configuration
KSQLDB_URL=http://localhost:8088
KSQLDB_TIMEOUT=30
KSQLDB_MAX_RETRIES=5

# Query timeout settings
KSQLDB_QUERY_TIMEOUT=30
KSQLDB_STREAM_QUERY_TIMEOUT=60
KSQLDB_CONNECTOR_QUERY_TIMEOUT=45
```

### Configuration Functions

```python
from ksqldb_config import get_ksqldb_config, get_ksqldb_config_with_custom_timeout

# Get default configuration
config = get_ksqldb_config()

# Get configuration with custom timeout
config = get_ksqldb_config_with_custom_timeout(timeout=60)
```

## Basic Usage

### Initialization

```python
from ksqldb_handler import KsqlDBHandler
from ksqldb_config import get_ksqldb_config

# Initialize with configuration
config = get_ksqldb_config()
ksqldb_handler = KsqlDBHandler(**config)

# Or initialize directly
ksqldb_handler = KsqlDBHandler(
    ksqldb_url="http://localhost:8088",
    timeout=30,
    max_retries=5
)
```

### Health Check

```python
# Check if ksqlDB server is healthy
is_healthy = ksqldb_handler.health_check()
if is_healthy:
    print("ksqlDB server is healthy!")
    
# Get server information
server_info = ksqldb_handler.get_server_info()
print(f"Server info: {server_info}")
```

### Creating Streams

```python
# Create a stream
stream_name = "user_events"
stream_config = """
CREATE STREAM user_events (
    user_id VARCHAR,
    event_type VARCHAR,
    timestamp BIGINT,
    metadata MAP<VARCHAR, VARCHAR>
) WITH (
    kafka_topic='user_events',
    value_format='JSON'
);
"""

success = ksqldb_handler.create_stream(stream_name, stream_config)
if success:
    print(f"Stream '{stream_name}' created successfully!")
```

### Creating Tables

```python
# Create a table
table_name = "user_profiles"
table_config = """
CREATE TABLE user_profiles (
    user_id VARCHAR PRIMARY KEY,
    username VARCHAR,
    email VARCHAR,
    created_at BIGINT
) WITH (
    kafka_topic='user_profiles',
    value_format='JSON'
);
"""

success = ksqldb_handler.create_table(table_name, table_config)
if success:
    print(f"Table '{table_name}' created successfully!")
```

### Creating Connectors

```python
# Create a sink connector
connector_name = "elasticsearch_sink"
connector_config = """
CREATE SINK CONNECTOR elasticsearch_sink WITH (
    'connector.class' = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
    'topics' = 'user_events',
    'connection.url' = 'http://elasticsearch:9200',
    'type.name' = 'user_event',
    'key.ignore' = 'true',
    'schema.ignore' = 'true'
);
"""

success = ksqldb_handler.create_sink_connector(connector_name, connector_config)
if success:
    print(f"Connector '{connector_name}' created successfully!")
```

### Inserting Data

```python
# Insert data into a stream
event_data = {
    "user_id": "user123",
    "event_type": "login",
    "timestamp": int(time.time() * 1000),
    "metadata": {
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0"
    }
}

success = ksqldb_handler.insert_data("user_events", event_data)
if success:
    print("Data inserted successfully!")
```

### Executing Queries

```python
# Execute a custom query
query = "SELECT user_id, event_type, timestamp FROM user_events EMIT CHANGES LIMIT 5;"
result = ksqldb_handler.execute_query(query)
if result:
    print(f"Query result: {result}")
```

### Listing Objects

```python
# List all streams
streams = ksqldb_handler.list_streams()
print(f"Streams: {streams}")

# List all tables
tables = ksqldb_handler.list_tables()
print(f"Tables: {tables}")

# List all connectors
connectors = ksqldb_handler.list_connectors()
print(f"Connectors: {connectors}")

# List all topics
topics = ksqldb_handler.list_topics()
print(f"Topics: {topics}")
```

### Describing Objects

```python
# Describe a stream
description = ksqldb_handler.describe_stream("user_events")
if description:
    print(f"Stream description: {description}")

# Describe a table
description = ksqldb_handler.describe_table("user_profiles")
if description:
    print(f"Table description: {description}")
```

### Dropping Objects

```python
# Drop a stream
success = ksqldb_handler.drop_stream("user_events", delete_topic=False)
if success:
    print("Stream dropped successfully!")

# Drop a table
success = ksqldb_handler.drop_table("user_profiles", delete_topic=False)
if success:
    print("Table dropped successfully!")

# Drop a connector
success = ksqldb_handler.drop_connector("elasticsearch_sink")
if success:
    print("Connector dropped successfully!")
```

## FastAPI Integration

The `ksqldb_integration.py` file provides FastAPI endpoints for all ksqlDB operations.

### Setup

```python
from fastapi import FastAPI
from ksqldb_integration import router

app = FastAPI()
app.include_router(router)
```

### Available Endpoints

- `POST /ksqldb/execute-query` - Execute ksqlDB queries
- `POST /ksqldb/create-stream` - Create streams
- `POST /ksqldb/create-table` - Create tables
- `POST /ksqldb/create-connector` - Create connectors
- `POST /ksqldb/insert-data` - Insert data into streams
- `GET /ksqldb/list-streams` - List all streams
- `GET /ksqldb/list-tables` - List all tables
- `GET /ksqldb/list-connectors` - List all connectors
- `GET /ksqldb/list-topics` - List all topics
- `GET /ksqldb/describe-stream/{stream_name}` - Describe a stream
- `GET /ksqldb/describe-table/{table_name}` - Describe a table
- `DELETE /ksqldb/drop-stream/{stream_name}` - Drop a stream
- `DELETE /ksqldb/drop-table/{table_name}` - Drop a table
- `DELETE /ksqldb/drop-connector/{connector_name}` - Drop a connector
- `GET /ksqldb/health` - Health check

### Example API Usage

```python
import requests

# Execute a query
response = requests.post("http://localhost:8000/ksqldb/execute-query", json={
    "query": "SHOW STREAMS;"
})
print(response.json())

# Create a stream
response = requests.post("http://localhost:8000/ksqldb/create-stream", json={
    "stream_name": "test_stream",
    "stream_config": "CREATE STREAM test_stream (id VARCHAR, message VARCHAR) WITH (kafka_topic='test', value_format='JSON');"
})
print(response.json())

# Insert data
response = requests.post("http://localhost:8000/ksqldb/insert-data", json={
    "stream_name": "test_stream",
    "data": {"id": "test123", "message": "Hello ksqlDB!"}
})
print(response.json())
```

## Advanced Examples

### Stream Processing

```python
# Create source stream for orders
orders_stream = "orders"
orders_config = """
CREATE STREAM orders (
    order_id VARCHAR,
    user_id VARCHAR,
    product_id VARCHAR,
    quantity INT,
    price DOUBLE,
    timestamp BIGINT
) WITH (
    kafka_topic='orders',
    value_format='JSON'
);
"""

ksqldb_handler.create_stream(orders_stream, orders_config)

# Create a table to track user order counts
user_orders_config = """
CREATE TABLE user_order_counts AS
SELECT user_id,
       COUNT(*) as order_count,
       SUM(quantity * price) as total_spent
FROM orders
GROUP BY user_id
EMIT CHANGES;
"""

ksqldb_handler.execute_query(user_orders_config)

# Insert sample data
sample_orders = [
    {
        "order_id": "order1",
        "user_id": "user1",
        "product_id": "prod1",
        "quantity": 2,
        "price": 29.99,
        "timestamp": int(time.time() * 1000)
    }
]

for order in sample_orders:
    ksqldb_handler.insert_data(orders_stream, order)
```

### Error Handling

```python
try:
    # Initialize ksqlDB handler
    config = get_ksqldb_config()
    ksqldb_handler = KsqlDBHandler(**config)
    
    # Health check
    if not ksqldb_handler.health_check():
        print("ksqlDB server is not healthy")
        return
    
    # Create stream
    success = ksqldb_handler.create_stream("test_stream", stream_config)
    if not success:
        print("Failed to create stream")
        return
        
    # Insert data
    success = ksqldb_handler.insert_data("test_stream", data)
    if not success:
        print("Failed to insert data")
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
- Retry only on specific exceptions (network errors)

### Connection Testing

The handler automatically tests the connection to ksqlDB on initialization:

```python
# Connection is tested automatically
ksqldb_handler = KsqlDBHandler(**config)
# If connection fails, appropriate error messages are logged
```

### Comprehensive Logging

All operations are logged with appropriate levels:

- INFO: Successful operations
- ERROR: Failed operations
- DEBUG: Detailed operation information

### Type Safety

The handler uses Python type hints for better code quality and IDE support.

## Best Practices

1. **Always check health before operations**: Use `health_check()` to ensure the server is available.

2. **Handle errors gracefully**: Wrap operations in try-catch blocks and handle failures appropriately.

3. **Use configuration files**: Store configuration in environment variables or configuration files.

4. **Monitor operations**: Use the logging functionality to monitor ksqlDB operations.

5. **Clean up resources**: Drop unused streams, tables, and connectors to free up resources.

6. **Use appropriate timeouts**: Set reasonable timeouts based on your ksqlDB server performance.

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if ksqlDB server is running and accessible.
2. **Query timeout**: Increase timeout values in configuration.
3. **Authentication errors**: Verify ksqlDB server configuration.
4. **Stream already exists**: Use `check_exists=True` parameter to avoid errors.

### Debug Mode

Enable debug logging to get detailed information about operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to the ksqlDB handler:

1. Follow the existing code structure and patterns
2. Add appropriate type hints
3. Include comprehensive error handling
4. Add logging for all operations
5. Update documentation for new features
6. Add tests for new functionality

## License

This ksqlDB handler follows the same license as the parent project. 
