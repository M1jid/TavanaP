# Kafka Handler

A comprehensive Kafka handler that provides a unified interface for both producing and consuming messages, with event-driven listening capabilities for FastAPI applications.

## Features

- **Unified Interface**: Single handler for both producer and consumer operations
- **Event-driven Listening**: Asynchronous message processing with callback functions
- **Batch Operations**: Efficient batch message production and consumption
- **Error Handling**: Built-in retry mechanisms and comprehensive error handling
- **FastAPI Integration**: Seamless integration with FastAPI applications
- **Connection Management**: Automatic connection pooling and health monitoring
- **Serialization**: Flexible message serialization/deserialization (JSON, string, bytes)
- **Configuration**: Environment-based configuration with sensible defaults
- **Context Manager**: Support for `with` statement usage
- **Background Tasks**: Utilities for running Kafka operations in background

## Installation

Ensure you have the required dependencies:

```bash
pip install aiokafka tenacity python-dotenv
```

## Configuration

The Kafka handler uses environment variables for configuration. Create a `.env` file or set the following environment variables:

```env
# Kafka Connection
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Producer Configuration
KAFKA_PRODUCER_ACKS=all
KAFKA_PRODUCER_RETRIES=3
KAFKA_PRODUCER_COMPRESSION_TYPE=snappy

# Consumer Configuration
KAFKA_CONSUMER_GROUP_ID=default-group
KAFKA_CONSUMER_AUTO_OFFSET_RESET=latest
KAFKA_CONSUMER_ENABLE_AUTO_COMMIT=true

# Event-driven Configuration
KAFKA_LISTENER_ENABLED=true
KAFKA_LISTENER_TOPICS=telegram_jobs,user_messages
KAFKA_LISTENER_GROUP_ID=telegram-workers

# Security (if using SASL/SSL)
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_SASL_USERNAME=your_username
KAFKA_SASL_PASSWORD=your_password
KAFKA_SSL_CA_LOCATION=/path/to/ca-cert
```

## Basic Usage

### Simple Producer

```python
import asyncio
from utils.kafka_handler import KafkaHandler

async def main():
    async with KafkaHandler() as kafka:
        # Produce a simple message
        result = await kafka.produce(
            topic="test-topic",
            value={"message": "Hello Kafka!"},
            key="test-key"
        )
        print(f"Message produced: {result}")

asyncio.run(main())
```

### Simple Consumer

```python
import asyncio
from utils.kafka_handler import KafkaHandler

async def main():
    async with KafkaHandler() as kafka:
        # Consume messages
        messages = await kafka.consume(
            topics=["test-topic"],
            group_id="my-consumer-group",
            timeout_ms=5000
        )
        
        for msg in messages:
            print(f"Received: {msg.value}")

asyncio.run(main())
```

## Event-driven Listening

### Basic Event Listener

```python
import asyncio
from utils.kafka_handler import KafkaHandler, KafkaMessage

async def handle_telegram_job(message: KafkaMessage):
    """Handle telegram job messages."""
    print(f"Processing telegram job: {message.value}")
    # Your business logic here

async def main():
    kafka = KafkaHandler()
    
    # Add listener
    kafka.add_listener("telegram_jobs", handle_telegram_job)
    
    # Start listening
    await kafka.start_listener(
        topics=["telegram_jobs"],
        group_id="telegram-workers"
    )
    
    # Keep running
    try:
        await asyncio.sleep(60)  # Run for 1 minute
    finally:
        await kafka.stop_listener()
        await kafka.close()

asyncio.run(main())
```

### Multiple Topic Listeners

```python
async def handle_telegram_job(message: KafkaMessage):
    print(f"📱 Telegram Job: {message.value}")

async def handle_user_message(message: KafkaMessage):
    print(f"💬 User Message: {message.value}")

async def handle_system_event(message: KafkaMessage):
    print(f"⚙️ System Event: {message.value}")

async def main():
    kafka = KafkaHandler()
    
    # Add multiple listeners
    kafka.add_listener("telegram_jobs", handle_telegram_job)
    kafka.add_listener("user_messages", handle_user_message)
    kafka.add_listener("system_events", handle_system_event)
    
    # Start listening to all topics
    await kafka.start_listener(
        topics=["telegram_jobs", "user_messages", "system_events"],
        group_id="multi-topic-consumer"
    )
    
    # Keep running
    await asyncio.sleep(60)

asyncio.run(main())
```

## FastAPI Integration

### Basic FastAPI Setup

```python
from fastapi import FastAPI, Depends
from utils.kafka_integration import KafkaIntegration, get_kafka_handler
from utils.kafka_handler import KafkaHandler, KafkaMessage

# Create FastAPI app
app = FastAPI()

# Setup Kafka integration
kafka_integration = KafkaIntegration(app=app)

# Add message handler
async def handle_telegram_job(message: KafkaMessage):
    print(f"Processing telegram job: {message.value}")

kafka_integration.add_listener("telegram_jobs", handle_telegram_job)

# Routes
@app.post("/send-message")
async def send_message(
    topic: str,
    message: dict,
    kafka: KafkaHandler = Depends(get_kafka_handler)
):
    result = await kafka.produce(topic, message)
    return {"status": "sent", "result": result}

@app.get("/kafka/health")
async def kafka_health(kafka: KafkaHandler = Depends(get_kafka_handler)):
    return await kafka.health_check()
```

### Advanced FastAPI Integration

```python
from fastapi import FastAPI
from utils.kafka_integration import KafkaIntegration, setup_telegram_kafka_listener

app = FastAPI()

# Create Kafka integration with custom config
kafka_integration = KafkaIntegration(
    app=app,
    auto_start_listener=True
)

# Setup telegram-specific listener
async def process_telegram_job(job_data: dict):
    """Process telegram job data."""
    # Your telegram processing logic here
    print(f"Processing telegram job: {job_data}")

# Setup the listener
await setup_telegram_kafka_listener(
    kafka_integration.get_kafka_handler(),
    process_telegram_job
)
```

## Batch Operations

### Batch Production

```python
async def main():
    async with KafkaHandler() as kafka:
        # Prepare batch messages
        messages = [
            {
                "topic": "batch-topic",
                "value": {"id": i, "data": f"Message {i}"},
                "key": f"key-{i}"
            }
            for i in range(10)
        ]
        
        # Produce batch
        results = await kafka.produce_batch(messages)
        print(f"Batch produced: {len(results)} messages")
```

### Batch Consumption

```python
async def main():
    async with KafkaHandler() as kafka:
        # Consume multiple messages at once
        messages = await kafka.consume(
            topics=["batch-topic"],
            group_id="batch-consumer",
            timeout_ms=5000,
            max_records=50
        )
        
        print(f"Consumed {len(messages)} messages")
        for msg in messages:
            print(f"Message: {msg.value}")
```

## Error Handling and Retry

The handler includes built-in retry mechanisms:

```python
async def main():
    async with KafkaHandler() as kafka:
        try:
            # This will automatically retry on failure
            result = await kafka.produce(
                topic="test-topic",
                value={"test": "data"}
            )
            print(f"Message produced: {result}")
        except Exception as e:
            print(f"Failed after retries: {e}")
        
        # Health check
        health = await kafka.health_check()
        print(f"Kafka health: {health}")
```

## Custom Configuration

### Custom Producer/Consumer Config

```python
# Custom configuration
custom_producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'acks': 'all',
    'retries': 5,
    'compression.type': 'gzip'
}

custom_consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'custom-group',
    'auto.offset.reset': 'earliest'
}

async with KafkaHandler(
    producer_config=custom_producer_config,
    consumer_config=custom_consumer_config
) as kafka:
    # Use with custom config
    result = await kafka.produce("topic", "message")
```

### Custom Serialization

```python
async with KafkaHandler(
    key_serializer='json',
    value_serializer='json',
    key_deserializer='json',
    value_deserializer='json'
) as kafka:
    # Messages will be automatically serialized/deserialized as JSON
    result = await kafka.produce("topic", {"data": "value"})
```

## Message Routing

### Content-based Routing

```python
async def route_message(message: KafkaMessage):
    """Route messages based on content."""
    data = message.value
    
    if 'telegram' in str(data).lower():
        print(f"📱 Routing to telegram handler: {data}")
    elif 'user' in str(data).lower():
        print(f"👤 Routing to user handler: {data}")
    elif 'system' in str(data).lower():
        print(f"⚙️ Routing to system handler: {data}")

async def main():
    async with KafkaHandler() as kafka:
        kafka.add_listener("routing-topic", route_message)
        await kafka.start_listener(["routing-topic"], "router-group")
        
        # Send test messages
        await kafka.produce("routing-topic", {"type": "telegram", "action": "send"})
        await kafka.produce("routing-topic", {"type": "user", "action": "login"})
        
        await asyncio.sleep(5)
```

## Background Tasks

### Periodic Message Production

```python
from utils.kafka_integration import KafkaBackgroundTask

async def main():
    kafka = KafkaHandler()
    background_task = KafkaBackgroundTask(kafka)
    
    # Start periodic producer
    await background_task.start_periodic_producer(
        topic="heartbeat",
        message_generator=lambda: {"timestamp": datetime.now().isoformat()},
        interval=30.0,  # Every 30 seconds
        task_name="heartbeat_producer"
    )
    
    # Keep running
    await asyncio.sleep(300)  # Run for 5 minutes
    
    # Stop the task
    await background_task.stop_task("heartbeat_producer")
    await kafka.close()
```

## Health Monitoring

### Health Check

```python
async def main():
    async with KafkaHandler() as kafka:
        health = await kafka.health_check()
        print(f"Kafka Health: {health}")
        
        # Health response example:
        # {
        #     'producer_connected': True,
        #     'consumer_connected': True,
        #     'listener_running': False,
        #     'timestamp': '2024-01-01T12:00:00'
        # }
```

## Integration with Existing Code

### Replacing Your Current Kafka Listener

Replace your current factory.py kafka listener:

```python
# OLD CODE (in factory.py):
async def kafka_listener():
    consumer = AIOKafkaConsumer(
        "telegram_jobs",
        bootstrap_servers="kafka:9092",
        group_id="telegram-workers"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await handle_kafka_message(msg)
    finally:
        await consumer.stop()

# NEW CODE (using KafkaHandler):
from utils.kafka_handler import KafkaHandler, KafkaMessage

async def handle_kafka_message(message: KafkaMessage):
    """Handle incoming Kafka messages."""
    print(f"Processing message: {message.value}")
    # Your existing message handling logic here

# In your FastAPI app startup:
kafka_handler = KafkaHandler()
kafka_handler.add_listener("telegram_jobs", handle_kafka_message)
await kafka_handler.start_listener(
    topics=["telegram_jobs"],
    group_id="telegram-workers"
)
```

### Using with Your Telegram Service

```python
# In your user_chat service:
from utils.kafka_handler import KafkaHandler

async def send_message_via_kafka(
    admin_phone: int,
    user_id: int,
    message: str
):
    """Send message via Kafka for processing."""
    async with KafkaHandler() as kafka:
        job_data = {
            "admin_phone": admin_phone,
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await kafka.produce("telegram_jobs", job_data)
        return result
```

## Best Practices

1. **Use Context Managers**: Always use `async with KafkaHandler()` for automatic cleanup
2. **Error Handling**: Wrap Kafka operations in try-catch blocks
3. **Health Monitoring**: Regularly check Kafka health in production
4. **Batch Operations**: Use batch operations for better performance
5. **Connection Pooling**: The handler manages connections automatically
6. **Serialization**: Choose appropriate serialization for your data types
7. **Group IDs**: Use meaningful consumer group IDs
8. **Topics**: Use descriptive topic names

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check bootstrap servers and network connectivity
2. **Serialization Errors**: Ensure data can be serialized with chosen method
3. **Consumer Group Issues**: Use unique group IDs for different consumers
4. **Memory Issues**: Monitor batch sizes and message volumes

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

- Adjust batch sizes based on your message volume
- Use compression for large messages
- Monitor consumer lag and adjust polling intervals
- Use appropriate acknowledgment settings

## API Reference

### KafkaHandler Methods

- `produce(topic, value, key=None, **kwargs)`: Produce a single message
- `produce_batch(messages)`: Produce multiple messages
- `consume(topics, group_id=None, **kwargs)`: Consume messages
- `add_listener(topic, callback)`: Add event listener
- `remove_listener(topic, callback)`: Remove event listener
- `start_listener(topics, group_id=None)`: Start event-driven listening
- `stop_listener()`: Stop event-driven listening
- `health_check()`: Check connection health
- `close()`: Close all connections

### Configuration Options

See `kafka_config.py` for all available configuration options.

## Examples

See `kafka_example.py` for comprehensive usage examples.

## Integration

See `kafka_integration.py` for FastAPI integration utilities.
