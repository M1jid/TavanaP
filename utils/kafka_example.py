"""
Kafka Handler Usage Examples

This file demonstrates various ways to use the KafkaHandler for both
producing and consuming messages, including event-driven listening.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from kafka_handler import KafkaHandler, KafkaMessage
from kafka_config import get_kafka_listener_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Basic Producer Usage
async def example_basic_producer():
    """Example of basic message production."""
    print("\n=== Basic Producer Example ===")
    
    async with KafkaHandler() as kafka:
        # Produce a simple message
        result = await kafka.produce(
            topic="test-topic",
            value={"message": "Hello Kafka!", "timestamp": datetime.now().isoformat()},
            key="test-key-1"
        )
        print(f"Message produced: {result}")
        
        # Produce multiple messages
        messages = [
            {
                "topic": "test-topic",
                "value": {"id": i, "data": f"Message {i}"},
                "key": f"key-{i}"
            }
            for i in range(5)
        ]
        
        results = await kafka.produce_batch(messages)
        print(f"Batch produced: {len(results)} messages")


# Example 2: Basic Consumer Usage
async def example_basic_consumer():
    """Example of basic message consumption."""
    print("\n=== Basic Consumer Example ===")
    
    async with KafkaHandler() as kafka:
        # Consume messages
        messages = await kafka.consume(
            topics=["test-topic"],
            group_id="example-consumer-group",
            timeout_ms=5000,
            max_records=10
        )
        
        print(f"Consumed {len(messages)} messages:")
        for msg in messages:
            print(f"  Topic: {msg.topic}, Key: {msg.key}, Value: {msg.value}")


# Example 3: Event-driven Listener with Callbacks
async def example_event_driven_listener():
    """Example of event-driven message listening."""
    print("\n=== Event-driven Listener Example ===")
    
    # Define callback functions
    async def handle_telegram_job(message: KafkaMessage):
        """Handle telegram job messages."""
        print(f"📱 Telegram Job: {message.value}")
        # Process the telegram job here
        # e.g., send message, process media, etc.
    
    async def handle_user_message(message: KafkaMessage):
        """Handle user message."""
        print(f"💬 User Message: {message.value}")
        # Process user message here
    
    async def handle_system_event(message: KafkaMessage):
        """Handle system events."""
        print(f"⚙️ System Event: {message.value}")
        # Process system event here
    
    # Create Kafka handler
    kafka = KafkaHandler()
    
    # Add listeners for different topics
    kafka.add_listener("telegram_jobs", handle_telegram_job)
    kafka.add_listener("user_messages", handle_user_message)
    kafka.add_listener("system_events", handle_system_event)
    
    try:
        # Start the listener
        await kafka.start_listener(
            topics=["telegram_jobs", "user_messages", "system_events"],
            group_id="event-driven-consumer"
        )
        
        # Simulate some messages being produced
        await asyncio.sleep(2)
        await kafka.produce("telegram_jobs", {"action": "send_message", "user_id": 12345})
        await kafka.produce("user_messages", {"user_id": 12345, "text": "Hello!"})
        await kafka.produce("system_events", {"event": "user_login", "timestamp": datetime.now().isoformat()})
        
        # Let the listener run for a bit
        await asyncio.sleep(5)
        
    finally:
        await kafka.stop_listener()
        await kafka.close()


# Example 4: FastAPI Integration Pattern
async def example_fastapi_integration():
    """Example showing how to integrate with FastAPI."""
    print("\n=== FastAPI Integration Example ===")
    
    # This would typically be in your FastAPI app
    kafka_handler = KafkaHandler()
    
    # Message handler for telegram jobs
    async def handle_telegram_message(message: KafkaMessage):
        """Handle incoming telegram job messages."""
        try:
            job_data = message.value
            print(f"Processing telegram job: {job_data}")
            
            # Your business logic here
            # e.g., send message via telegram client
            # await telegram_client.send_message(job_data)
            
        except Exception as e:
            logger.error(f"Error processing telegram message: {e}")
    
    # Add the listener
    kafka_handler.add_listener("telegram_jobs", handle_telegram_message)
    
    # Start listening (this would be in your FastAPI startup event)
    await kafka_handler.start_listener(
        topics=["telegram_jobs"],
        group_id="telegram-workers"
    )
    
    print("FastAPI Kafka listener started")
    
    # Simulate some work
    await asyncio.sleep(3)
    
    # Cleanup (this would be in your FastAPI shutdown event)
    await kafka_handler.stop_listener()
    await kafka_handler.close()


# Example 5: Error Handling and Retry
async def example_error_handling():
    """Example of error handling and retry mechanisms."""
    print("\n=== Error Handling Example ===")
    
    async with KafkaHandler() as kafka:
        try:
            # This will retry automatically if it fails
            result = await kafka.produce(
                topic="test-topic",
                value={"test": "data"},
                key="error-test-key"
            )
            print(f"Message produced successfully: {result}")
            
        except Exception as e:
            print(f"Failed to produce message after retries: {e}")
        
        # Health check
        health = await kafka.health_check()
        print(f"Kafka health: {health}")


# Example 6: Custom Configuration
async def example_custom_config():
    """Example with custom configuration."""
    print("\n=== Custom Configuration Example ===")
    
    # Custom producer config
    custom_producer_config = {
        'bootstrap.servers': 'localhost:9092',
        'acks': 'all',
        'retries': 5,
        'compression.type': 'gzip'
    }
    
    # Custom consumer config
    custom_consumer_config = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'custom-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    
    async with KafkaHandler(
        producer_config=custom_producer_config,
        consumer_config=custom_consumer_config,
        key_serializer='json',
        value_serializer='json'
    ) as kafka:
        
        # Produce with custom config
        result = await kafka.produce(
            topic="custom-topic",
            value={"custom": "data"},
            key={"custom": "key"}
        )
        print(f"Custom config message produced: {result}")


# Example 7: Batch Operations
async def example_batch_operations():
    """Example of batch message operations."""
    print("\n=== Batch Operations Example ===")
    
    async with KafkaHandler() as kafka:
        # Prepare batch messages
        batch_messages = []
        for i in range(10):
            batch_messages.append({
                "topic": "batch-topic",
                "value": {
                    "id": i,
                    "message": f"Batch message {i}",
                    "timestamp": datetime.now().isoformat()
                },
                "key": f"batch-key-{i}",
                "headers": {"source": "batch-example"}
            })
        
        # Produce batch
        results = await kafka.produce_batch(batch_messages)
        print(f"Batch produced: {len(results)} messages")
        
        # Consume batch
        messages = await kafka.consume(
            topics=["batch-topic"],
            group_id="batch-consumer",
            timeout_ms=5000,
            max_records=20
        )
        print(f"Batch consumed: {len(messages)} messages")


# Example 8: Message Routing (like your existing kafka_router)
async def example_message_routing():
    """Example of message routing based on content."""
    print("\n=== Message Routing Example ===")
    
    async def route_message(message: KafkaMessage):
        """Route messages based on content."""
        try:
            data = message.value
            
            if 'telegram' in str(data).lower():
                print(f"📱 Routing to telegram handler: {data}")
                # Route to telegram processing
                
            elif 'user' in str(data).lower():
                print(f"👤 Routing to user handler: {data}")
                # Route to user processing
                
            elif 'system' in str(data).lower():
                print(f"⚙️ Routing to system handler: {data}")
                # Route to system processing
                
            else:
                print(f"❓ Unknown message type: {data}")
                
        except Exception as e:
            logger.error(f"Error routing message: {e}")
    
    async with KafkaHandler() as kafka:
        # Add routing listener
        kafka.add_listener("routing-topic", route_message)
        
        # Start listener
        await kafka.start_listener(
            topics=["routing-topic"],
            group_id="router-group"
        )
        
        # Send test messages
        await kafka.produce("routing-topic", {"type": "telegram", "action": "send_message"})
        await kafka.produce("routing-topic", {"type": "user", "action": "login"})
        await kafka.produce("routing-topic", {"type": "system", "action": "backup"})
        await kafka.produce("routing-topic", {"type": "unknown", "action": "test"})
        
        # Let it process
        await asyncio.sleep(3)
        
        await kafka.stop_listener()


# Main function to run all examples
async def main():
    """Run all examples."""
    print("🚀 Kafka Handler Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_basic_producer()
        await example_basic_consumer()
        await example_event_driven_listener()
        await example_fastapi_integration()
        await example_error_handling()
        await example_custom_config()
        await example_batch_operations()
        await example_message_routing()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    asyncio.run(main())
