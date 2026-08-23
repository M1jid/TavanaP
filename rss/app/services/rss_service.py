"""
RSS Service

This module contains the main RSS service that handles feed fetching,
processing, and distribution with proper error handling and logging.
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

# Logging
import logging
logger = logging.getLogger(__name__)

from utils.redis_wrapper import RedisWrapper
from utils.ksqldb_handler import KsqlDBHandler
from utils.kafka_router import KafkaRouter
from utils.elastic_handler import ElasticHandler
from utils.db_handler import get_rss_channels, update_rss_channel
from app.services.feed_fetcher import FeedFetcher
from app.services.feed_processor import FeedProcessor

import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
connector = aiohttp.TCPConnector(ssl=ssl_context)

@dataclass
class ServiceStats:
    """Service statistics"""
    total_feeds_processed: int = 0
    total_messages_sent: int = 0
    last_processing_time: Optional[float] = None
    errors_count: int = 0
    start_time: Optional[float] = None


class RSSService:
    """
    Main RSS service that orchestrates feed processing and message distribution.
    
    This service follows clean architecture principles with proper separation
    of concerns and dependency injection.
    """
    
    def __init__(
        self,
        redis_db: RedisWrapper,
        ksql_handler: KsqlDBHandler,
        kafka_router: KafkaRouter,
        proxy_server: Tuple,
        elastic_handler: ElasticHandler
    ):
        """Initialize the RSS service with dependencies"""
        self.redis_db = redis_db
        self.ksql_handler = ksql_handler
        self.kafka_router = kafka_router
        self.proxy_server = proxy_server
        self.elastic_handler = elastic_handler

        self.feed_fetcher = None
        self.feed_processor = None
        
        self.stats = ServiceStats()
        self.is_running = True
        self.processing_task = None

        # Initialize sub-services
        self.feed_fetcher = FeedFetcher(proxy_server=proxy_server)
        self.feed_processor = FeedProcessor(
            redis_db=redis_db,
            ksql_handler=ksql_handler,
            kafka_router=kafka_router,
            elastic_handler=elastic_handler
        )

        # Initialize session
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/117.0.0.0 Safari/537.36"
            }
        )

        self.stats.start_time = time.time()
        self.is_running = True
        
    async def start_service(self):
        # Start background processing
        self.processing_task = asyncio.create_task(self._background_processing())
        logger.info("RSS Service initialized successfully")
        
    async def shutdown_service(self):
        """Shutdown the RSS service gracefully"""
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()

        logger.info("RSS Service shutdown completed")
    
    async def _background_processing(self):
        """Background task for continuous feed processing"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Get RSS channels from database
                feed_urls = get_rss_channels()
                if not feed_urls:
                    logger.warning("No RSS feeds found in database")
                    await asyncio.sleep(120)
                    continue
                
                # Process all feeds
                await self.process_feeds(feed_urls)
                
                processing_time = time.time() - start_time
                self.stats.last_processing_time = processing_time
                
                logger.info(f"Feed processing completed in {processing_time:.2f}s. Waiting 60 minutes...")
                await asyncio.sleep(3600)

            except Exception as e:
                self.stats.errors_count += 1
                logger.error(f"Error in background processing: {e}")
                await asyncio.sleep(30)  # Shorter wait on error
    
    async def process_feeds(self, feed_urls: List[Dict]) -> None:
        """Process multiple RSS feeds concurrently"""
        if not self.feed_fetcher or not self.feed_processor or not self.session:
            raise RuntimeError("Service not properly initialized")
        
        semaphore = asyncio.Semaphore(10)

        tasks = [
            self._process_single_feed(feed_data, self.session, semaphore) 
            for feed_data in feed_urls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful processing
        successful = sum(1 for r in results if not isinstance(r, Exception))
        self.stats.total_feeds_processed += successful
        
        # Log errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing feed {feed_urls[i].get('key', 'unknown')}: {result}")
    
    async def _process_single_feed(self, feed_data: Dict, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> None:
        """Process a single RSS feed"""
        async with semaphore:
            try:
                url = feed_data.get("value_rss")
                key = feed_data.get("key")
                if not url or not key:
                    logger.warning(f"Invalid feed data: {feed_data}")
                    return

                blocked = feed_data.get("blocked", False)
                last_update = feed_data.get("last_update")
                if blocked:
                    try:
                        last_update_dt = (
                            last_update if isinstance(last_update, datetime)
                            else datetime.fromisoformat(last_update)
                        )
                    except Exception as parse_err:
                        logger.warning(f"Could not parse last_update for {key}: {parse_err}")
                        last_update_dt = None

                    if last_update_dt and last_update_dt < datetime.utcnow() - timedelta(days=1):
                        logger.info(f"Trying to re-check blocked feed: {key}")
                        try:
                            test_feed = await self.feed_fetcher.fetch_feed(session, url)
                            if test_feed and test_feed.entries:
                                logger.info(f"Feed {key} is reachable again. Unblocking.")
                                feed_data["blocked"] = False
                                update_rss_channel(feed_data["id"], {
                                    "blocked": False,
                                    "last_update": datetime.utcnow().isoformat()
                                })
                                logger.info(f"Feed {key} unblocked successfully.")
                            else:
                                logger.info(f"Feed {key} still has no entries. Keeping blocked.")
                                update_rss_channel(feed_data["id"], {
                                    "last_update": datetime.utcnow().isoformat()
                                })
                                return
                        except Exception as unblock_err:
                            logger.warning(f"Failed to re-check blocked feed {key}: {unblock_err}")
                            return
                        
                    else:
                        # Blocked but not older than 1 days
                        logger.info(f"Feed {key} is still within 1 day of last update. Skipping.")
                        return
                else:
                    feed = await self.feed_fetcher.fetch_feed(self.session, url)
                    if not feed or not feed.entries:
                        logger.warning(f"No entries found in feed: {url}")
                        update_rss_channel(feed_data["id"], {
                            "blocked": True,
                            "last_update": datetime.utcnow().isoformat()
                        })
                        logger.info(f"Marking feed '{key}' as blocked due to no entries.")
                        return

                    processed_count = await self.feed_processor.process_feed_entries(
                        feed.entries, key, url
                    )
                    self.stats.total_messages_sent += processed_count

                    update_rss_channel(feed_data["id"], {
                        "last_update": datetime.utcnow().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error processing feed {feed_data.get('key', 'unknown')}: {e}")
                update_rss_channel(feed_data["id"], {
                    "blocked": True,
                    "last_update": datetime.utcnow().isoformat()
                })
                logger.info(f"Marking feed '{key}' as blocked due to error in processing feed.")
                raise
    
    async def get_service_info(self) -> Dict:
        """Get service information and statistics"""
        uptime = time.time() - self.stats.start_time if self.stats.start_time else 0
        
        return {
            "service": "rss",
            "version": "1.0.0",
            "status": "running" if self.is_running else "stopped",
            "uptime_seconds": int(uptime),
            "statistics": {
                "total_feeds_processed": self.stats.total_feeds_processed,
                "total_messages_sent": self.stats.total_messages_sent,
                "errors_count": self.stats.errors_count,
                "last_processing_time_seconds": self.stats.last_processing_time
            }
        }
    
    async def add_feed_channel(self, channel_data: Dict) -> Dict:
        """Add a new RSS feed channel"""
        # This would typically involve database operations
        # For now, we'll just return a success response
        return {
            "status": "success",
            "message": "Feed channel added successfully",
            "channel_key": channel_data.get("key")
        }
    
    async def remove_feed_channel(self, channel_key: str) -> Dict:
        """Remove an RSS feed channel"""
        # This would typically involve database operations
        return {
            "status": "success",
            "message": "Feed channel removed successfully",
            "channel_key": channel_key
        }
