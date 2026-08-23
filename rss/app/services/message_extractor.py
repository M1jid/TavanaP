"""
Message Extractor Service

This module handles the extraction and formatting of RSS feed entries
into structured messages for distribution.
"""

import time
import re
import hashlib
import logging

from typing import Any, List, Optional
from utils.date_time_mapper import get_time, get_jalali_date, create_date_object
from utils.models_handler import get_sentiment

logger = logging.getLogger(__name__)


class MessageExtractor:
    """
    Service for extracting and formatting RSS feed entries into structured messages.
    """
    
    def __init__(self, entry: Any, key: str):
        """
        Initialize the message extractor.
        
        Args:
            entry: RSS feed entry object
            key: Channel key/identifier
        """
        self.entry = entry
        self.key = key
    
    def get_title(self) -> str:
        """Extract and clean the entry title."""
        title = self.entry.get("title", "")
        if title:
            return title.replace("'", "''")
        return ''
    
    def get_link(self) -> str:
        """Extract the entry link, with fallback to ID."""
        link = self.entry.get("link", None)
        if not link or link == '':
            link = self.entry.get("id", None)
        return link or ''
    
    def get_date(self) -> str:
        """Get the entry publication date."""
        return self.entry.published
    
    def get_summary(self) -> str:
        """Extract and clean the entry summary."""
        summary = self.entry.get("summary", "")
        # Remove HTML tags
        summary = re.sub(r"<.*?>", "", summary)
        # Clean up whitespace
        summary = summary.replace('\n', '').strip()
        if summary:
            return summary.replace("'", "''")
        return ''
    
    def get_author(self) -> str:
        """Extract the entry author."""
        author = self.entry.get("author", "")
        if author:
            return author.replace("'", "''")
        return ''
    
    def get_id(self) -> str:
        """Get the entry ID."""
        return self.entry.get("id", "")
    
    def get_timestamp(self) -> int:
        """Get the entry timestamp."""
        return int(time.mktime(self.entry.get("published_parsed", time.gmtime())))
    
    def get_tags(self) -> List[str]:
        """Extract tags/categories from the entry."""
        tags = self.entry.get("tags", None)
        if tags:
            return self._parse_tags(tags)
        
        # Fallback to category
        tags = self.entry.get("category", None)
        if tags:
            return self._parse_tags(tags)
        
        return []
    
    def _parse_tags(self, tags: Any) -> List[str]:
        """Parse tags from various formats."""
        if isinstance(tags, list):
            if tags and isinstance(tags[0], str):
                return tags
            if tags and isinstance(tags[0], dict):
                return [tag.get('term', '') for tag in tags if tag.get('term')]
        elif isinstance(tags, str):
            return [tags]
        elif isinstance(tags, dict):
            term = tags.get('term')
            return [term] if term else []
        
        return []

    def get_image(self) -> Optional[str]:
        """Extract image URL from the entry, if available."""
        # Check media_content (common for feeds with images/videos)
        media = self.entry.get("media_content", [])
        if media and isinstance(media, list):
            url = media[0].get("url")
            if url:
                return url
        
        # Check media_thumbnail
        thumbnail = self.entry.get("media_thumbnail", [])
        if thumbnail and isinstance(thumbnail, list):
            url = thumbnail[0].get("url")
            if url:
                return url
        
        # Check links with rel="enclosure"
        links = self.entry.get("links", [])
        if links and isinstance(links, list):
            for link in links:
                if link.get("rel") == "enclosure" and "image" in link.get("type", ""):
                    return link.get("href")
        
        # Check direct fields like 'image' or 'thumbnail'
        if "image" in self.entry:
            if isinstance(self.entry["image"], dict):
                return self.entry["image"].get("href") or self.entry["image"].get("url")
            return self.entry["image"]
        
        if "thumbnail" in self.entry:
            return self.entry["thumbnail"]
    
        return ""

    def extract(self, channel_key: str, feed_url: str):
        """
        Extract and format the RSS entry into structured messages.
        
        Returns:
            Tuple of (telegram_draft, telegram_message_data)
        """
        # Extract basic information
        title = self.get_title()
        source = self.get_key()
        link = self.get_link()
        date_str = self.get_date()
        summary = self.get_summary()
        author = self.get_author()
        timestamp = self.get_timestamp()
        tags = self.get_tags()
        image = self.get_image()

        # Sentiment analysis
        try:
            sentiment_resp = get_sentiment(title + " " + summary)
            sentiment = sentiment_resp.get("result", None)
            if sentiment == "خطا":
                sentiment = "خنثی"
        except Exception as e:
            sentiment = None
            logger.error(f"Error getting sentiment: {e}")
        
        # Parse and format date
        parsed_date = create_date_object(date_str=date_str)
        date = get_jalali_date(parsed_date=parsed_date)
        time_str = get_time(parsed_date=parsed_date)
        
        # Format tags
        tags_str = '-'.join([tag for tag in tags if tag])
        tags_str = tags_str.replace("'", "''")
        
        # Create Telegram message format
        rss_context = self._create_telegram_message(
            title=title,
            source=source,
            link=link,
            date=date,
            time=time_str,
            author=author,
            tags=tags_str
        )
        
        # Create message data structures
        formatted_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        telegram_draft = {
            'message': rss_context,
            'content': title + summary,
            'resource': 'rss',
        }
        
        ksql_data = {
            'fetch_time': timestamp,
            'sentiment': sentiment,
            'channel_name': source,
            'date': formatted_date,
            'summary': summary,
            'id': f'{channel_key}-{hashlib.md5(link.encode()).hexdigest()}',
            'link': link,
            'title': title,
            'author': author,
            'tags': tags_str,
            'image': image, 
        }
        
        return telegram_draft, ksql_data
    
    def _create_telegram_message(
        self, 
        title: str, 
        source: str, 
        link: str, 
        date: str, 
        time: str, 
        author: str, 
        tags: str
    ) -> str:
        """
        Create a formatted Telegram message.
        """
        message = (
            f"📍{title}\n\n\n"
            f"🔹*منبع: *{source}\n"
            f"🖥 *آدرس خبر: *[لینک مطلب]({link})\n"
            f"🗓 *تاریخ انتشار: *{date}\n"
            f"🗓 *ساعت انتشار: *{time}\n"
            f"🗂بستر: سایت‌های خبری\n"
        )
        
        if author:
            message += f"\n🖋 *نویسنده:* {author}\n"
        
        return message
    
    def get_key(self) -> str:
        """Get the channel key."""
        return self.key
