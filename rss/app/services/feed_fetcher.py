"""
Feed Fetcher Service

This module handles RSS feed fetching with proper error handling,
retry logic, and proxy support.
"""

import asyncio
import aiohttp
import feedparser
import requests
import base64
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed
from bs4 import BeautifulSoup
import traceback

# Logging
import logging
logger = logging.getLogger(__name__)


class FeedFetcher:
    """
    Service for fetching RSS feeds with proper error handling and proxy support.
    """
    
    def __init__(self, proxy_server):
        self.proxy_server = "http://192.168.10.53:10808"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def fetch_feed(self, session: aiohttp.ClientSession, url: str) -> Optional[Any]:
        """
        Fetch an RSS feed from the given URL.
        
        Args:
            session: aiohttp session for making requests
            url: RSS feed URL
            
        Returns:
            Parsed feed object or None if failed
        """

        kwargs = {"timeout": 30}
        if '.ir' not in url:
            kwargs["proxy"] = self.proxy_server

        try:
            async with session.get(url, **kwargs) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch feed {url}: HTTP {response.status}")
                    return None

                text = await response.text()
                feed = feedparser.parse(text)

                if not feed.entries:
                    logger.warning(f"Feed fetched but no entries found: {url}, keys={list(feed.keys())}, bozo={feed.bozo}")

                return feed

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching feed {url}")
        except aiohttp.client_exceptions.ClientConnectorDNSError as e:
            logger.error(f"DNS error fetching feed {url}: {e}")
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error fetching feed {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching feed {url} [{type(e).__name__}]: {e}")
            logger.error(traceback.format_exc())

        return None
    
    # async def get_open_graph_image(self, session: aiohttp.ClientSession, url: str) -> str:
    #     """
    #     Extract Open Graph image from a webpage.
        
    #     Args:
    #         session: aiohttp session
    #         url: Webpage URL
            
    #     Returns:
    #         Open Graph image URL or empty string
    #     """
    #     try:
    #         async with session.get(url, timeout=10) as response:
    #             if response.status == 200:
    #                 html_content = await response.text()
    #                 soup = BeautifulSoup(html_content, 'html.parser')
    #                 og_image_tag = soup.find('meta', property='og:image')
    #                 if og_image_tag:
    #                     return og_image_tag.get('content', '')
    #     except Exception as e:
    #         logger.debug(f"Error fetching Open Graph image for {url}: {e}")
        
    #     return ''
    
    async def download_channel_logo(self, key: str, website_link: str, first_item: Dict[str, Any]) -> str:
        """
        Download channel logo/favicon using Google's favicon service.
        
        Args:
            key: Channel key
            website_link: Website URL
            first_item: First RSS entry for fallback
            
        Returns:
            Base64 encoded image or empty string
        """
        logger.info(f'Downloading favicon for channel: {key}')
        
        if not website_link:
            website_link = first_item.get('link', '')
        
        if not website_link:
            logger.warning(f"No website link available for channel {key}")
            return ''
        
        try:
            # Use Google's favicon service
            favicon_url = f"https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url={website_link}&size=128"
            
            response = requests.get(favicon_url, timeout=10)
            if response.status_code == 200:
                base64_str = base64.b64encode(response.content).decode("utf-8")
                logger.info(f"Successfully downloaded favicon for {key}")
                return base64_str
            else:
                logger.warning(f"Failed to download favicon for {key}: HTTP {response.status_code}")
                return ''
                
        except Exception as e:
            logger.error(f"Error downloading favicon for {key}: {e}")
            return ''
    
    async def get_rss_source_details(self, rss_source: Dict[str, Any], feed: Any) -> Dict[str, Any]:
        """
        Extract RSS source details from feed metadata.
        
        Args:
            rss_source: RSS source configuration
            feed: Parsed feed object
            
        Returns:
            Dictionary with source details
        """
        url = rss_source.get('value_rss', '')
        key = rss_source.get('key', '')
        
        details = {
            'title': getattr(feed.feed, 'title', key),
            'channel_name': key,
            'link': key,
            'rss': url,
            'image': url  # Placeholder, will be updated with actual favicon
        }
        
        # Download favicon if we have entries
        if feed.entries:
            favicon = await self.download_channel_logo(
                key=key,
                website_link=key,
                first_item=feed.entries[0]
            )
            if favicon:
                details['image'] = favicon
        
        return details 
