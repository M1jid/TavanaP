"""
Feed Processor Service

This module handles the processing of RSS feed entries, including
message extraction, deduplication, and distribution to various systems.
"""

import os
import signal
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Logging
import logging
logger = logging.getLogger(__name__)

from utils.redis_wrapper import RedisWrapper
from utils.ksqldb_handler import KsqlDBHandler
from utils.kafka_router import KafkaRouter
from utils.elastic_handler import ElasticHandler
from app.services.message_extractor import MessageExtractor


class FeedProcessor:
    """
    Service for processing RSS feed entries and distributing messages.
    """
    
    def __init__(
        self,
        redis_db: RedisWrapper,
        ksql_handler: KsqlDBHandler,
        kafka_router: KafkaRouter,
        elastic_handler: ElasticHandler
    ):
        self.redis_db = redis_db
        self.ksql_handler = ksql_handler
        self.kafka_router = kafka_router
        self.elastic_handler = elastic_handler
    
    def get_last_read_news_link(self, url: str) -> Optional[str]:
        """
        Get the last processed news link for a feed URL from Redis.
        
        Args:
            url: RSS feed URL
            
        Returns:
            Last processed link or None
        """
        try:
            logger.info(f"Getting last read link for: {url}")
            last_read_message = self.redis_db.get(key=url)
            return last_read_message
        except TypeError:
            logger.error("Error getting last read link: TypeError")
            return None
        except Exception as e:
            logger.error(f"Error getting last read link: {e}")
            return None
    
    def update_last_read_link(self, url: str, link: str) -> None:
        """
        Update the last processed link for a feed URL in Redis.
        
        Args:
            url: RSS feed URL
            link: Last processed link
        """
        try:
            self.redis_db.store(key=url, value=link)
            logger.debug(f"Updated last read link for {url}: {link}")
        except Exception as e:
            logger.error(f"Error updating last read link: {e}")
    
    async def process_feed_entries(
        self, 
        entries: List[Any], 
        channel_key: str, 
        feed_url: str
    ) -> int:
        """
        Process RSS feed entries and distribute messages.
        
        Args:
            entries: List of RSS feed entries
            channel_key: Channel identifier
            feed_url: RSS feed URL
            
        Returns:
            Number of processed messages
        """
        if not entries:
            logger.warning(f"No entries to process for channel {channel_key}")
            return 0
        
        last_link = self.get_last_read_news_link(url=feed_url)
        processed_count = 0
        
        # Update last read link with the most recent entry
        if entries:
            self.update_last_read_link(url=feed_url, link=entries[0].get("link", ""))
        
        for entry in entries:
            try:
                # Stop processing if we reach the last processed entry
                if entry.link == last_link:
                    logger.info(f"Reached last processed entry for {channel_key}")
                    break
                
                # Extract and process message
                extractor = MessageExtractor(entry=entry, key=channel_key)
                telegram_draft, elastic_data = extractor.extract(channel_key=channel_key, feed_url=feed_url)
                
                # Validate message before processing
                # if not self._validate_message(telegram_draft):
                #     logger.warning(f"Invalid message for {channel_key}: {telegram_draft.get('title', 'No title')}")
                #     continue
                
                # Store in KSQL database
                await self._store_message_in_ksql(elastic_data)
                
                # Send to Kafka for distribution
                draft_date = elastic_data.get("date")
                if draft_date:
                    draft_date = datetime.fromisoformat(draft_date)
                    cutoff = datetime.utcnow() - timedelta(days=1)
                    if draft_date < cutoff:
                        logger.info(
                            f"Skipping send the old message to kafka for '{channel_key}' "
                            f"(date: {draft_date})"
                        )
                        continue

                await self._send_to_kafka(telegram_draft)
                
                processed_count += 1
                logger.debug(f"Processed message: {telegram_draft.get('title', 'No title')}")
                
            except Exception as e:
                logger.error(f"Error processing entry for {channel_key}: {e}")
                continue
        
        logger.info(f"Processed {processed_count} messages for channel {channel_key}")
        return processed_count
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate a processed message before distribution.
        
        Args:
            message: Message to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['link', 'title', 'channel_name']
        for field in required_fields:
            if not message.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check link length (Telegram limitation)
        link = message.get('link', '')
        if len(link.encode('utf-8')) >= 512:
            logger.warning(f"Link too long: {len(link.encode('utf-8'))} bytes")
            return False
        
        return True
    
    async def _store_message_in_ksql(self, message: Dict[str, Any]) -> None:
        """
        Store message in KSQL database.
        
        Args:
            message: Message to store
        """
        try:
            self.ksql_handler.insert_data(stream_name='RSS_MESSAGES3', data=message)
            logger.debug(f"Stored message in KSQL: {message.get('title', 'No title')}")
        except Exception as e:
            logger.error(f"Error storing message in KSQL: {e}")
            # In production, you might want to handle this differently
            # For now, we'll terminate the process as in the original code
            os.kill(os.getpid(), signal.SIGINT)
    
    async def _send_to_kafka(self, message: Dict[str, Any]) -> None:
        """
        Send message to Kafka for distribution.
        
        Args:
            message: Message to send
        """
        try:
            self.kafka_router.route_message(message_obj=message)
            logger.debug(f"Sent message to Kafka: {message.get('content', 'No content')[:50]}...")
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
    
    async def store_channel_details(self, channel_details: Dict[str, Any]) -> None:
        """
        Store RSS channel details in KSQL database.
        
        Args:
            channel_details: Channel details to store
        """
        try:
            self.ksql_handler.insert_data(stream_name='RSS_CHANNELS', data=channel_details)
            logger.info(f"Stored channel details: {channel_details.get('channel_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error storing channel details: {e}")
            # In production, you might want to handle this differently
            os.kill(os.getpid(), signal.SIGINT) 
            