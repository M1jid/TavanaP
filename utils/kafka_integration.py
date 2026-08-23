"""
Kafka Integration for FastAPI Applications

This module provides integration utilities for using KafkaHandler with FastAPI,
including startup/shutdown events, dependency injection, and background tasks.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.base import BaseHTTPMiddleware

from .kafka_handler import KafkaHandler, KafkaMessage
from .kafka_config import get_kafka_listener_config

logger = logging.getLogger(__name__)


class KafkaIntegration:
    """
    Kafka integration manager for FastAPI applications.
    
    This class manages Kafka connections, listeners, and provides
    dependency injection for FastAPI routes.
    """
    
    def __init__(
        self,
        app: Optional[FastAPI] = None,
        kafka_handler: Optional[KafkaHandler] = None,
        auto_start_listener: bool = True
    ):
        """
        Initialize Kafka integration.
        
        Args:
            app: FastAPI application instance
            kafka_handler: Custom KafkaHandler instance (creates default if None)
            auto_start_listener: Whether to automatically start the listener on startup
        """
        self.app = app
        self.kafka_handler = kafka_handler or KafkaHandler()
        self.auto_start_listener = auto_start_listener
        self._listener_started = False
        
        if self.app:
            self._setup_app()
    
    def _setup_app(self):
        """Setup FastAPI app with Kafka integration."""
        if not self.app:
            return
        
        # Add startup and shutdown events
        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()
        
        # Add health check endpoint
        @self.app.get("/health/kafka")
        async def kafka_health():
            return await self.kafka_handler.health_check()
        
        logger.info("Kafka integration setup completed for FastAPI app")
    
    async def startup(self):
        """Startup Kafka connections and listeners."""
        try:
            if self.auto_start_listener:
                await self.start_listener()
            logger.info("Kafka integration started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka integration: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown Kafka connections and listeners."""
        try:
            await self.stop_listener()
            await self.kafka_handler.close()
            logger.info("Kafka integration shutdown completed")
        except Exception as e:
            logger.error(f"Error during Kafka integration shutdown: {e}")
    
    async def start_listener(self, topics: Optional[list] = None, group_id: Optional[str] = None):
        """Start the Kafka listener."""
        if self._listener_started:
            logger.warning("Kafka listener is already started")
            return
        
        listener_config = get_kafka_listener_config()
        topics = topics or listener_config['topics']
        group_id = group_id or listener_config['group_id']
        
        await self.kafka_handler.start_listener(topics=topics, group_id=group_id)
        self._listener_started = True
        logger.info(f"Kafka listener started for topics: {topics}")
    
    async def stop_listener(self):
        """Stop the Kafka listener."""
        if not self._listener_started:
            return
        
        await self.kafka_handler.stop_listener()
        self._listener_started = False
        logger.info("Kafka listener stopped")
    
    def add_listener(self, topic: str, callback: Callable[[KafkaMessage], Awaitable[None]]):
        """Add a listener callback for a topic."""
        self.kafka_handler.add_listener(topic, callback)
        logger.info(f"Added listener for topic: {topic}")
    
    def remove_listener(self, topic: str, callback: Callable[[KafkaMessage], Awaitable[None]]):
        """Remove a listener callback for a topic."""
        self.kafka_handler.remove_listener(topic, callback)
        logger.info(f"Removed listener for topic: {topic}")
    
    async def produce_message(
        self,
        topic: str,
        value: Any,
        key: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Produce a message to Kafka."""
        return await self.kafka_handler.produce(topic, value, key, **kwargs)
    
    def get_kafka_handler(self) -> KafkaHandler:
        """Get the Kafka handler instance."""
        return self.kafka_handler


# Dependency injection function
def get_kafka_handler() -> KafkaHandler:
    """
    FastAPI dependency to get Kafka handler instance.
    
    This should be used in your route handlers to access Kafka functionality.
    """
    # This would typically get the handler from a global instance or app state
    # For now, we'll create a new instance (in real usage, you'd store this globally)
    return KafkaHandler()


# Middleware for Kafka request logging
class KafkaLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests to Kafka."""
    
    def __init__(self, app, kafka_handler: KafkaHandler, topic: str = "http_requests"):
        super().__init__(app)
        self.kafka_handler = kafka_handler
        self.topic = topic
    
    async def dispatch(self, request, call_next):
        """Process request and log to Kafka."""
        start_time = asyncio.get_event_loop().time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = asyncio.get_event_loop().time() - start_time
        
        # Log to Kafka
        try:
            await self.kafka_handler.produce(
                topic=self.topic,
                value={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "timestamp": asyncio.get_event_loop().time()
                },
                key=f"{request.method}:{request.url.path}"
            )
        except Exception as e:
            logger.error(f"Failed to log request to Kafka: {e}")
        
        return response


# Utility functions for common patterns

async def setup_telegram_kafka_listener(
    kafka_handler: KafkaHandler,
    telegram_client_callback: Callable[[Dict[str, Any]], Awaitable[None]]
):
    """
    Setup a Kafka listener specifically for Telegram jobs.
    
    Args:
        kafka_handler: Kafka handler instance
        telegram_client_callback: Callback function to handle telegram jobs
    """
    async def handle_telegram_job(message: KafkaMessage):
        """Handle incoming telegram job messages."""
        try:
            job_data = message.value
            logger.info(f"Processing telegram job: {job_data}")
            await telegram_client_callback(job_data)
        except Exception as e:
            logger.error(f"Error processing telegram job: {e}")
    
    kafka_handler.add_listener("telegram_jobs", handle_telegram_job)
    logger.info("Telegram Kafka listener setup completed")


async def setup_user_message_listener(
    kafka_handler: KafkaHandler,
    user_message_callback: Callable[[Dict[str, Any]], Awaitable[None]]
):
    """
    Setup a Kafka listener for user messages.
    
    Args:
        kafka_handler: Kafka handler instance
        user_message_callback: Callback function to handle user messages
    """
    async def handle_user_message(message: KafkaMessage):
        """Handle incoming user messages."""
        try:
            message_data = message.value
            logger.info(f"Processing user message: {message_data}")
            await user_message_callback(message_data)
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
    
    kafka_handler.add_listener("user_messages", handle_user_message)
    logger.info("User message Kafka listener setup completed")


# Example FastAPI app setup
def create_fastapi_app_with_kafka() -> FastAPI:
    """
    Example of creating a FastAPI app with Kafka integration.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(title="Kafka-Integrated API", version="1.0.0")
    
    # Create Kafka integration
    kafka_integration = KafkaIntegration(app=app)
    
    # Add middleware for request logging
    app.add_middleware(
        KafkaLoggingMiddleware,
        kafka_handler=kafka_integration.get_kafka_handler(),
        topic="http_requests"
    )
    
    # Example routes
    @app.post("/send-message")
    async def send_message(
        topic: str,
        message: Dict[str, Any],
        kafka: KafkaHandler = Depends(get_kafka_handler)
    ):
        """Send a message to Kafka topic."""
        result = await kafka.produce(topic, message)
        return {"status": "sent", "result": result}
    
    @app.get("/kafka/health")
    async def kafka_health(kafka: KafkaHandler = Depends(get_kafka_handler)):
        """Check Kafka health."""
        return await kafka.health_check()
    
    return app


# Context manager for temporary Kafka operations
@asynccontextmanager
async def kafka_context():
    """
    Context manager for temporary Kafka operations.
    
    Usage:
        async with kafka_context() as kafka:
            await kafka.produce("topic", "message")
    """
    kafka = KafkaHandler()
    try:
        yield kafka
    finally:
        await kafka.close()


# Background task utilities
class KafkaBackgroundTask:
    """Utility class for running Kafka operations in background tasks."""
    
    def __init__(self, kafka_handler: KafkaHandler):
        self.kafka_handler = kafka_handler
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def start_periodic_producer(
        self,
        topic: str,
        message_generator: Callable[[], Dict[str, Any]],
        interval: float = 60.0,
        task_name: str = "periodic_producer"
    ):
        """
        Start a background task that periodically produces messages.
        
        Args:
            topic: Kafka topic to produce to
            message_generator: Function that generates message data
            interval: Interval between messages in seconds
            task_name: Name for the background task
        """
        if task_name in self._tasks:
            logger.warning(f"Task {task_name} is already running")
            return
        
        async def producer_loop():
            while True:
                try:
                    message = message_generator()
                    await self.kafka_handler.produce(topic, message)
                    logger.debug(f"Periodic message produced to {topic}")
                except Exception as e:
                    logger.error(f"Error in periodic producer: {e}")
                
                await asyncio.sleep(interval)
        
        self._tasks[task_name] = asyncio.create_task(producer_loop())
        logger.info(f"Started periodic producer task: {task_name}")
    
    async def stop_task(self, task_name: str):
        """Stop a background task."""
        if task_name in self._tasks:
            self._tasks[task_name].cancel()
            try:
                await self._tasks[task_name]
            except asyncio.CancelledError:
                pass
            del self._tasks[task_name]
            logger.info(f"Stopped background task: {task_name}")
    
    async def stop_all_tasks(self):
        """Stop all background tasks."""
        for task_name in list(self._tasks.keys()):
            await self.stop_task(task_name)
        logger.info("All background tasks stopped")
