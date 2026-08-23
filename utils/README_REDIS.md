# Redis Handler

A comprehensive Redis handler class that provides a high-level interface for Redis operations using the `redis-py` library.

## Features

- **Connection Management**: Automatic connection pooling and retry mechanisms
- **Key-Value Operations**: Set, get, delete, and check existence of keys
- **Data Structures**: Support for lists, sets, and hashes
- **Pub/Sub Messaging**: Publish and subscribe to channels
- **TTL Management**: Set and check expiration times
- **Error Handling**: Comprehensive error handling with logging
- **JSON Serialization**: Automatic serialization/deserialization of complex data types
- **Context Manager**: Support for `with` statement usage

## Installation

Ensure you have the required dependencies:

```bash
pip install redis tenacity
```

## Configuration

The Redis handler uses environment variables for configuration. Create a `.env` file or set the following environment variables:

```env
# Redis Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password  # Optional
REDIS_SSL=false
REDIS_SSL_CERT_REQS=none

# Connection Settings
REDIS_CONNECT_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true
REDIS_MAX_CONNECTIONS=10

# Default TTL Settings (in seconds)
REDIS_DEFAULT_TTL=3600
REDIS_CACHE_TTL=1800
REDIS_SESSION_TTL=86400
```

## Basic Usage

### Initialization

```python
from redis_handler import RedisHandler
from redis_config import get_redis_config

# Using configuration
config = get_redis_config()
redis_handler = RedisHandler(**config)

# Or direct initialization
redis_handler = RedisHandler(
    host='localhost',
    port=6379,
    db=0,
    password=None
)
```

### Key-Value Operations

```python
# Set a simple value
redis_handler.set("user:1", "John Doe")

# Set with TTL (expires in 1 hour)
redis_handler.set("session:123", "session_data", ttl=3600)

# Set complex data (automatically JSON serialized)
user_data = {
    "id": 1,
    "name": "Jane Smith",
    "email": "jane@example.com"
}
redis_handler.set("user:2", user_data)

# Get values
user = redis_handler.get("user:1")
user_data = redis_handler.get("user:2")

# Check if key exists
exists = redis_handler.exists("user:1")

# Delete keys
deleted = redis_handler.delete("user:1", "user:2")

# Set expiration
redis_handler.expire("key", 3600)

# Get TTL
ttl = redis_handler.ttl("key")
```

### List Operations

```python
# Push items to list
redis_handler.lpush("queue:tasks", "task1", "task2", "task3")
redis_handler.rpush("queue:tasks", "task4", "task5")

# Get list length
length = redis_handler.llen("queue:tasks")

# Get all items
all_tasks = redis_handler.lrange("queue:tasks")

# Pop items
task = redis_handler.lpop("queue:tasks")  # From left
task = redis_handler.rpop("queue:tasks")  # From right
```

### Set Operations

```python
# Add items to set
redis_handler.sadd("tags:article1", "python", "redis", "database")

# Get all members
tags = redis_handler.smembers("tags:article1")

# Check membership
has_tag = redis_handler.sismember("tags:article1", "python")

# Remove items
redis_handler.srem("tags:article1", "database")
```

### Hash Operations

```python
# Set hash fields
redis_handler.hset("user:profile:1", "name", "Alice Johnson")
redis_handler.hset("user:profile:1", "age", 30)
redis_handler.hset("user:profile:1", "preferences", {"theme": "dark"})

# Get individual fields
name = redis_handler.hget("user:profile:1", "name")
preferences = redis_handler.hget("user:profile:1", "preferences")

# Get all fields
profile = redis_handler.hgetall("user:profile:1")

# Delete fields
redis_handler.hdel("user:profile:1", "age")
```

### Pub/Sub Operations

```python
# Publish messages
redis_handler.publish("news:tech", "New Redis version released!")

# Publish complex data
news_item = {
    "title": "Redis 7.0 Released",
    "content": "Major performance improvements"
}
redis_handler.publish("news:tech", news_item)

# Subscribe to channels
pubsub = redis_handler.subscribe("news:tech")
# Note: In a real application, you would listen for messages
```

### Utility Operations

```python
# Get keys matching pattern
test_keys = redis_handler.keys("test:*")
all_keys = redis_handler.keys("*")

# Get Redis server information
info = redis_handler.info("server")

# Ping Redis
is_alive = redis_handler.ping()

# Flush database (use with caution!)
redis_handler.flushdb()
```

### Context Manager Usage

```python
from redis_handler import RedisHandler

with RedisHandler(host='localhost', port=6379) as redis_handler:
    redis_handler.set("key", "value")
    value = redis_handler.get("key")
    # Connection automatically closed when exiting context
```

## Error Handling

The Redis handler includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Timeout Errors**: Configurable retry mechanisms
- **Serialization Errors**: Graceful handling of JSON serialization issues
- **Logging**: Detailed logging for debugging and monitoring

## Advanced Features

### Retry Mechanism

The handler uses the `tenacity` library for retry logic:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((redis.ConnectionError, redis.TimeoutError)),
    reraise=True
)
def execute_operation(self, operation_func, *args, **kwargs):
    return operation_func(*args, **kwargs)
```

### JSON Serialization

Complex data types are automatically serialized to JSON:

```python
# This will be automatically serialized
data = {
    "user": {"id": 1, "name": "John"},
    "timestamp": "2024-01-01T00:00:00Z"
}
redis_handler.set("complex:data", data)

# This will be automatically deserialized
retrieved_data = redis_handler.get("complex:data")
```

### Connection Pooling

The handler uses Redis connection pooling for better performance:

```python
self.pool = redis.ConnectionPool(
    host=host,
    port=port,
    db=db,
    max_connections=max_connections,
    # ... other configuration
)
```

## Examples

See `redis_example.py` for comprehensive examples of all operations.

## Best Practices

1. **Use Context Managers**: Always use the `with` statement when possible to ensure proper connection cleanup.

2. **Handle Errors**: Always wrap Redis operations in try-catch blocks.

3. **Use Appropriate TTL**: Set TTL for temporary data to prevent memory issues.

4. **Monitor Performance**: Use the `info()` method to monitor Redis performance.

5. **Use Connection Pooling**: The handler automatically manages connection pooling.

6. **Serialize Complex Data**: Let the handler handle JSON serialization for complex data types.

## Troubleshooting

### Connection Issues

- Ensure Redis server is running
- Check host and port configuration
- Verify network connectivity
- Check firewall settings

### Performance Issues

- Monitor connection pool size
- Use appropriate TTL values
- Consider using pipelining for bulk operations
- Monitor Redis memory usage

### Serialization Issues

- Ensure data is JSON serializable
- Handle custom objects appropriately
- Use string values for simple data

## API Reference

### Constructor Parameters

- `host` (str): Redis host address
- `port` (int): Redis port number
- `db` (int): Redis database number
- `password` (str, optional): Redis password
- `ssl` (bool): Whether to use SSL connection
- `ssl_cert_reqs` (str): SSL certificate requirements
- `connect_timeout` (int): Connection timeout in seconds
- `socket_timeout` (int): Socket timeout in seconds
- `socket_connect_timeout` (int): Socket connect timeout in seconds
- `retry_on_timeout` (bool): Whether to retry on timeout
- `max_connections` (int): Maximum number of connections in the pool
- `decode_responses` (bool): Whether to decode responses to strings

### Key Methods

- `set(key, value, ttl=None, nx=False, xx=False)`: Set a key-value pair
- `get(key, default=None)`: Get a value by key
- `delete(*keys)`: Delete one or more keys
- `exists(*keys)`: Check if keys exist
- `expire(key, ttl)`: Set expiration time
- `ttl(key)`: Get remaining TTL
- `lpush(key, *values)`: Push values to left of list
- `rpush(key, *values)`: Push values to right of list
- `lpop(key, count=1)`: Pop values from left of list
- `rpop(key, count=1)`: Pop values from right of list
- `lrange(key, start=0, end=-1)`: Get range of list elements
- `sadd(key, *values)`: Add values to set
- `srem(key, *values)`: Remove values from set
- `smembers(key)`: Get all set members
- `sismember(key, value)`: Check set membership
- `hset(key, field, value)`: Set hash field
- `hget(key, field, default=None)`: Get hash field
- `hgetall(key)`: Get all hash fields
- `publish(channel, message)`: Publish message to channel
- `subscribe(*channels)`: Subscribe to channels
- `keys(pattern="*")`: Get keys matching pattern
- `flushdb()`: Flush current database
- `info(section=None)`: Get Redis server information
- `ping()`: Ping Redis server
- `close()`: Close Redis connection 