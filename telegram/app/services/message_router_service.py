"""
Message Routing Service

This service handles routing of Telegram messages to appropriate channels
based on content matching and routing rules.
"""

import json
from typing import List, Optional

from app.telegram.extractors.channel_message import ChannelMessageExtractor
from utils.date_time_mapper import get_time, get_jalali_date
from app.startup import kafka_producer, channels_router
BLOCKED_RESOURCES = [
    1319925154,
    1294206528,
    1440421814,
    1413234537,
    1453655321,
    1956100570
]



def _add_keywords_to_context(telegram_context: str, channel: dict) -> str:
    """Add matched keywords to the telegram context."""
    musts = []
    for roles in channel.get('matched_roles', []):
        if 'lable' in roles:  # keeping original field name
            musts.extend(roles['lable'] or [])
        else:
            musts.extend(roles.get('must') or [])
    
    if musts:
        musts = '-'.join(sorted(set(musts)))
        telegram_context += f"📑 <b>کلیدواژه:</b> {musts}\n"
    
    return telegram_context


async def _process_matches(message, entity, username: Optional[str], text: str, matches: List[dict]) -> None:
    """Process matched channels and send messages to Kafka."""
    # Build telegram context
    if username:
        link = f"https://t.me/{username}/{message.id}"
    else:
        link = f"https://t.me/c/{entity.id}/{message.id}"

    source = entity.title
    date = get_jalali_date(message.date)
    time = get_time(message.date)

    telegram_context = (
        f"📍{text}\n\n\n"
        f"🔹*منبع: *{source}\n"
        f"🖥 *آدرس خبر: *[لینک مطلب]({link})\n"
        f"🗓 *تاریخ انتشار: *{date}\n"
        f"⏰ *ساعت انتشار: *{time}\n"
        f"🗂بستر: تلگرام\n"
    )

    for channel in matches:
        channel_id = channel['channel_id']
        
        # Add keywords to context if available
        telegram_context_with_keywords = _add_keywords_to_context(telegram_context, channel)
        
        payload = {
            'channel_id': channel_id,
            'content': text,
            'message': telegram_context_with_keywords,
            'resource': 'telegram',
        }

        kafka_producer.produce(str(channel_id), json.dumps(payload).encode("utf-8"))
        kafka_producer.flush()


async def route_message(message, entity, username: Optional[str], channel_ids: List[int]) -> None:
    """
    Route a message to appropriate channels based on content matching.
    
    Args:
        message: The Telegram message object
        entity: The Telegram entity (channel/group)
        username: Optional username of the entity
        channel_ids: List of channel IDs that the client is monitoring
    """
    # Handle new message forwarding if entity is not blocked or group message
    if entity.id in channel_ids and entity.id not in BLOCKED_RESOURCES:
        text = ChannelMessageExtractor.extract_entities(obj=message)['CLEANED_MESSAGE']
        matches = channels_router.match_channels(text)
        
        if matches:
            await _process_matches(message, entity, username, text, matches)
