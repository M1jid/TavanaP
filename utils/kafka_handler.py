"""
Kafka Handler for unified producer and consumer operations with event-driven listening.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, List, Any, Union, Callable, Awaitable
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .kafka_config import (
    get_kafka_producer_config,
    get_kafka_consumer_config,
    get_kafka_listener_config,
    KAFKA_MAX_RETRIES,
    KAFKA_RETRY_DELAY,
    KAFKA_RETRY_BACKOFF,
    KAFKA_KEY_SERIALIZER,
    KAFKA_VALUE_SERIALIZER,
    KAFKA_KEY_DESERIALIZER,
    KAFKA_VALUE_DESERIALIZER
)

logger = logging.getLogger(__name__)


class SerializationType(Enum):
    """Serialization types for Kafka messages."""
    JSON = "json"
    STRING = "string"
    BYTES = "bytes"


@dataclass
class KafkaMessage:
    """Kafka message data structure."""
    topic: str
    key: Optional[Union[str, bytes]] = None
    value: Optional[Union[str, bytes, Dict, List]] = None
    partition: Optional[int] = None
    offset: Optional[int] = None
    timestamp: Optional[datetime] = None
    headers: Optional[Dict[str, str]] = None


class KafkaHandler:
    """
    Unified Kafka handler for both producing and consuming messages.
    
    This class provides methods to:
    - Produce messages to Kafka topics
    - Consume messages from Kafka topics
    - Event-driven message listening with callbacks
    - Batch operations for better performance
    - Error handling and retry mechanisms
    - Connection management and health monitoring
    - Message serialization/deserialization
    """
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        producer_config: Optional[Dict[str, Any]] = None,
        consumer_config: Optional[Dict[str, Any]] = None,
        key_serializer: str = KAFKA_KEY_SERIALIZER,
        value_serializer: str = KAFKA_VALUE_SERIALIZER,
        key_deserializer: str = KAFKA_KEY_DESERIALIZER,
        value_deserializer: str = KAFKA_VALUE_DESERIALIZER
    ):
        """
        Initialize Kafka handler with connection parameters.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (overrides config if provided)
            producer_config: Custom producer configuration (overrides default config)
            consumer_config: Custom consumer configuration (overrides default config)
            key_serializer: Serialization type for message keys
            value_serializer: Serialization type for message values
            key_deserializer: Deserialization type for message keys
            value_deserializer: Deserialization type for message values
        """
        # Get base configurations
        self._producer_config = producer_config or get_kafka_producer_config()
        self._consumer_config = consumer_config or get_kafka_consumer_config()
        
        # Override bootstrap servers if provided
        if bootstrap_servers:
            self._producer_config['bootstrap_servers'] = bootstrap_servers
            self._consumer_config['bootstrap_servers'] = bootstrap_servers
        
        # Serialization settings
        self.key_serializer = SerializationType(key_serializer)
        self.value_serializer = SerializationType(value_serializer)
        self.key_deserializer = SerializationType(key_deserializer)
        self.value_deserializer = SerializationType(value_deserializer)
        
        # Connection objects
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._listener_callbacks: Dict[str, List[Callable[[KafkaMessage], Awaitable[None]]]] = {}
        self._is_listening = False
        
        logger.info(f"KafkaHandler initialized with bootstrap servers: {self._producer_config['bootstrap_servers']}")
    
    # Serialization/Deserialization Methods
    
    def _serialize_key(self, key: Any) -> Optional[bytes]:
        """Serialize message key."""
        if key is None:
            return None
        
        if self.key_serializer == SerializationType.JSON:
            return json.dumps(key).encode('utf-8')
        elif self.key_serializer == SerializationType.STRING:
            return str(key).encode('utf-8')
        elif self.key_serializer == SerializationType.BYTES:
            return key if isinstance(key, bytes) else str(key).encode('utf-8')
        else:
            return str(key).encode('utf-8')
    
    def _serialize_value(self, value: Any) -> Optional[bytes]:
        """Serialize message value."""
        if value is None:
            return None
        
        if self.value_serializer == SerializationType.JSON:
            return json.dumps(value).encode('utf-8')
        elif self.value_serializer == SerializationType.STRING:
            return str(value).encode('utf-8')
        elif self.value_serializer == SerializationType.BYTES:
            return value if isinstance(value, bytes) else str(value).encode('utf-8')
        else:
            return str(value).encode('utf-8')
    
    def _deserialize_key(self, key: bytes) -> Any:
        """Deserialize message key."""
        if key is None:
            return None
        
        if self.key_deserializer == SerializationType.JSON:
            return json.loads(key.decode('utf-8'))
        elif self.key_deserializer == SerializationType.STRING:
            return key.decode('utf-8')
        elif self.key_deserializer == SerializationType.BYTES:
            return key
        else:
            return key.decode('utf-8')
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize message value."""
        if value is None:
            return None
        
        if self.value_deserializer == SerializationType.JSON:
            return json.loads(value.decode('utf-8'))
        elif self.value_deserializer == SerializationType.STRING:
            return value.decode('utf-8')
        elif self.value_deserializer == SerializationType.BYTES:
            return value
        else:
            return value.decode('utf-8')
    
    # Connection Management
    
    async def _get_producer(self) -> AIOKafkaProducer:
        """Get or create producer connection."""
        if self._producer is None or self._producer._closed:
            self._producer = AIOKafkaProducer(**self._producer_config)
            await self._producer.start()
            logger.info("Kafka producer connected")
        return self._producer
    
    async def _get_consumer(self, group_id: Optional[str] = None) -> AIOKafkaConsumer:
        """Get or create consumer connection."""
        try:
            config = self._consumer_config.copy()
            if group_id:
                config['group_id'] = group_id
            
            # Always create a new consumer to avoid configuration caching issues
            if self._consumer:
                try:
                    await self._consumer.stop()
                except Exception:
                    pass  # Ignore errors when stopping old consumer
            
            logger.info(f"Creating consumer with config keys: {list(config.keys())}")
            logger.info(f"Bootstrap servers: {config.get('bootstrap_servers')}")
            logger.info(f"Group ID: {config.get('group_id')}")
            
            self._consumer = AIOKafkaConsumer(**config)
            logger.info("Consumer object created, starting...")
            await self._consumer.start()
            logger.info(f"Kafka consumer connected with group_id: {config['group_id']}")
            return self._consumer
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            logger.error(f"Consumer config was: {config}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def close(self):
        """Close all connections."""
        if self._producer and not self._producer._closed:
            await self._producer.stop()
            logger.info("Kafka producer disconnected")
        
        if self._consumer and not self._consumer._closed:
            await self._consumer.stop()
            logger.info("Kafka consumer disconnected")
        
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            logger.info("Kafka listener stopped")
    
    # Producer Methods
    
    @retry(
        stop=stop_after_attempt(KAFKA_MAX_RETRIES),
        wait=wait_exponential(multiplier=KAFKA_RETRY_DELAY, max=KAFKA_RETRY_BACKOFF),
        retry=retry_if_exception_type((KafkaError, KafkaTimeoutError))
    )
    async def produce(
        self,
        topic: str,
        value: Any,
        key: Optional[Any] = None,
        partition: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        timestamp_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Produce a single message to Kafka topic.
        
        Args:
            topic: Target topic name
            value: Message value
            key: Message key (optional)
            partition: Target partition (optional)
            headers: Message headers (optional)
            timestamp_ms: Message timestamp in milliseconds (optional)
        
        Returns:
            dict: Producer result with topic, partition, offset
        """
        producer = await self._get_producer()
        
        serialized_key = self._serialize_key(key)
        serialized_value = self._serialize_value(value)
        
        try:
            result = await producer.send_and_wait(
                topic=topic,
                value=serialized_value,
                key=serialized_key,
                partition=partition,
                headers=headers,
                timestamp_ms=timestamp_ms
            )
            
            logger.debug(f"Message produced to topic {topic}, partition {result.partition}, offset {result.offset}")
            return {
                'topic': result.topic,
                'partition': result.partition,
                'offset': result.offset,
                'timestamp': result.timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to produce message to topic {topic}: {e}")
            raise
    
    async def produce_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Produce multiple messages in batch.
        
        Args:
            messages: List of message dictionaries with keys: topic, value, key, partition, headers, timestamp_ms
        
        Returns:
            list: List of producer results
        """
        producer = await self._get_producer()
        results = []
        
        for msg in messages:
            try:
                result = await self.produce(
                    topic=msg['topic'],
                    value=msg['value'],
                    key=msg.get('key'),
                    partition=msg.get('partition'),
                    headers=msg.get('headers'),
                    timestamp_ms=msg.get('timestamp_ms')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to produce message in batch: {e}")
                results.append({'error': str(e)})
        
        return results
    
    # Consumer Methods
    
    async def consume(
        self,
        topics: Union[str, List[str]],
        group_id: Optional[str] = None,
        timeout_ms: int = 1000,
        max_records: int = 100
    ) -> List[KafkaMessage]:
        """
        Consume messages from Kafka topics.
        
        Args:
            topics: Topic name or list of topic names
            group_id: Consumer group ID (optional)
            timeout_ms: Poll timeout in milliseconds
            max_records: Maximum number of records to fetch
        
        Returns:
            list: List of KafkaMessage objects
        """
        consumer = await self._get_consumer(group_id)
        
        if isinstance(topics, str):
            topics = [topics]
        
        await consumer.subscribe(topics)
        
        try:
            msg_pack = await consumer.getmany(timeout_ms=timeout_ms, max_records=max_records)
            messages = []
            
            for topic_partition, records in msg_pack.items():
                for record in records:
                    message = KafkaMessage(
                        topic=record.topic,
                        key=self._deserialize_key(record.key),
                        value=self._deserialize_value(record.value),
                        partition=record.partition,
                        offset=record.offset,
                        timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else None,
                        headers=dict(record.headers) if record.headers else None
                    )
                    messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to consume messages from topics {topics}: {e}")
            raise
    
    # Event-driven Listener Methods
    
    def add_listener(self, topic: str, callback: Callable[[KafkaMessage], Awaitable[None]]):
        """
        Add a callback function for a specific topic.
        
        Args:
            topic: Topic name to listen to
            callback: Async function to call when message is received
        """
        if topic not in self._listener_callbacks:
            self._listener_callbacks[topic] = []
        self._listener_callbacks[topic].append(callback)
        logger.info(f"Added listener for topic: {topic}")
    
    def remove_listener(self, topic: str, callback: Callable[[KafkaMessage], Awaitable[None]]):
        """
        Remove a callback function for a specific topic.
        
        Args:
            topic: Topic name
            callback: Callback function to remove
        """
        if topic in self._listener_callbacks:
            try:
                self._listener_callbacks[topic].remove(callback)
                logger.info(f"Removed listener for topic: {topic}")
            except ValueError:
                logger.warning(f"Callback not found for topic: {topic}")
    
    async def start_listener(
        self,
        topics: Optional[List[str]] = None,
        group_id: Optional[str] = None,
        poll_timeout: float = 1.0
    ):
        """
        Start event-driven message listening.
        
        Args:
            topics: List of topics to listen to (uses config default if None)
            group_id: Consumer group ID (uses config default if None)
            poll_timeout: Poll timeout in seconds
        """
        if self._is_listening:
            logger.warning("Listener is already running")
            return
        
        if not topics:
            listener_config = get_kafka_listener_config()
            topics = listener_config['topics']
            group_id = group_id or listener_config['group_id']
            poll_timeout = listener_config['poll_timeout']
        
        self._is_listening = True
        self._listener_task = asyncio.create_task(
            self._listener_loop(topics, group_id, poll_timeout)
        )
        logger.info(f"Started Kafka listener for topics: {topics}")
    
    async def stop_listener(self):
        """Stop event-driven message listening."""
        if not self._is_listening:
            return
        
        self._is_listening = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped Kafka listener")
    
    async def _listener_loop(
        self,
        topics: List[str],
        group_id: str,
        poll_timeout: float
    ):
        """Internal listener loop for event-driven consumption."""
        try:
            logger.info(f"Getting consumer for group_id: {group_id}")
            consumer = await self._get_consumer(group_id)
            if consumer is None:
                logger.error("Failed to create consumer - consumer is None")
                return
            
            logger.info(f"Consumer created successfully, subscribing to topics: {topics}")
            
            # Subscribe to topics (subscribe is synchronous, not async)
            consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to setup consumer for topics {topics}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return
        
        try:
            while self._is_listening:
                try:
                    msg_pack = await consumer.getmany(timeout_ms=int(poll_timeout * 1000))
                    
                    for topic_partition, records in msg_pack.items():
                        for record in records:
                            message = KafkaMessage(
                                topic=record.topic,
                                key=self._deserialize_key(record.key),
                                value=self._deserialize_value(record.value),
                                partition=record.partition,
                                offset=record.offset,
                                timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else None,
                                headers=dict(record.headers) if record.headers else None
                            )
                            
                            # Call registered callbacks
                            if record.topic in self._listener_callbacks:
                                for callback in self._listener_callbacks[record.topic]:
                                    try:
                                        await callback(message)
                                    except Exception as e:
                                        logger.error(f"Error in callback for topic {record.topic}: {e}")
                
                except Exception as e:
                    logger.error(f"Error in listener loop: {e}")
                    await asyncio.sleep(1)  # Brief pause before retrying
        
        finally:
            if consumer:
                try:
                    await consumer.stop()
                except Exception as e:
                    logger.warning(f"Error stopping consumer: {e}")
    
    # Health and Monitoring Methods
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Kafka connection health.
        
        Returns:
            dict: Health status information
        """
        health = {
            'producer_connected': False,
            'consumer_connected': False,
            'listener_running': self._is_listening,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self._producer and not self._producer._closed:
                # Try to get metadata to test connection
                await self._producer.client.cluster()
                health['producer_connected'] = True
        except Exception as e:
            logger.warning(f"Producer health check failed: {e}")
        
        try:
            if self._consumer and not self._consumer._closed:
                # Try to get metadata to test connection
                if hasattr(self._consumer, 'client') and self._consumer.client:
                    await self._consumer.client.cluster()
                    health['consumer_connected'] = True
                else:
                    # Consumer exists but client might not be ready
                    health['consumer_connected'] = True
        except Exception as e:
            logger.warning(f"Consumer health check failed: {e}")
        
        return health
    
    # Context Manager Support
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
