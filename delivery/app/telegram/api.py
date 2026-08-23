# Telebot
from telebot.async_telebot import AsyncTeleBot
from requests.exceptions import SSLError, ConnectionError
from telebot import apihelper

# Kafka
from confluent_kafka import Producer, Consumer

from utils.redis_wrapper import RedisWrapper
from app.config import KAFKA_TOPIC

# Additions
import functools
import os
import json
import time
import asyncio
import requests
import re
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import aiohttp

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils.kafka_dispatcher import Worker


class TelegramBotWorker(Worker):
    def __init__(self, redis_client: RedisWrapper):
        self.token_to_bot = {}
        self.session_map = {}
        self.redis_client = redis_client
        self.channel_to_bots = {}
        self.proxy = 'http://192.168.10.53:10808'
        self.reload_bots()
        self.fill_channel_timestamps()
        self.MAX_MESSAGE_LENGTH = 4096
        self.allowed_tags = {
            "b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
            "span", "tg-spoiler", "code", "pre", "blockquote", "a"
        }

    def create_session(self):
        """Create a new requests session with retry logic and connection pooling."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_maxsize=10)
        session.mount("https://", adapter)
        return session

    def fill_channel_timestamps(self):
        for channel_id, bot_tokens in self.channel_to_bots.items():
            for bot_token in bot_tokens:
                last_sent_key = f"bot:{channel_id}:{bot_token}:next_use"
                next_use = self.redis_client.get(key=last_sent_key)
                if isinstance(next_use, int) or (isinstance(next_use, str) and next_use.isdigit()):
                    self.redis_client.store(key=last_sent_key, value=int(next_use) + 3)
                else:
                    self.redis_client.store(key=last_sent_key, value=int(time.time()) + 3)

    def reload_bots(self):
        """Load bot configurations and initialize bots with fresh sessions."""
        import os
        logger.info(os.listdir('conf'))
        with open('conf/routing_rules.json', "r", encoding="utf-8") as file:
            configs = json.load(file)
        self.channel_to_bots = {config['channel_id']: [bot['token'] for bot in config['bot_tokens']] for config in configs}
        logger.info(f"Loaded {len(self.channel_to_bots)} channels with bot tokens.")
        logger.info(self.channel_to_bots)

    def safe_html(self, text):
        def replace_tag(match):
            tag_content = match.group(1)
            tag = tag_content.split()[0].lower().strip('/')
            if tag in self.allowed_tags:
                return f"<{tag_content}>"
            else:
                return f"&lt;{tag_content}&gt;"

        # Step 1: Escape all '<' and '>' first
        text = text.replace('&', '&amp;')  # Important! Must escape & first
        text = text.replace('<', '&lt;').replace('>', '&gt;')

        # Step 2: Re-open allowed tags
        text = re.sub(r'&lt;([^&<>]+)&gt;', replace_tag, text)

        return text


    async def find_bot(self, channel_id, retries=5):
        for _ in range(retries):
            bot_tokens = self.channel_to_bots.get(channel_id, [])
            for bot_token in bot_tokens:
                if self.is_bot_available(channel_id, bot_token):
                    return bot_token
            await asyncio.sleep(3)
        raise Exception(f"No available bot found for {channel_id}")

    def is_bot_available(self, channel_id, bot_token):
        next_use_key = f"bot:{channel_id}:{bot_token}:next_use"
        next_use = self.redis_client.get(key=next_use_key)
        if next_use:
            next_use_time = float(next_use)
            if time.time() > int(next_use_time):
                return True
        return False

    def mark_bot_used(self, channel_id, bot_token):
        last_sent_key = f"bot:{channel_id}:{bot_token}:next_use"
        self.redis_client.store(key=last_sent_key, value=time.time()+4)

    async def send_message(self, channel_id, message, resource):
        """
        Send a message to a Telegram channel using the given bot token.
        Returns True if successful, False if it should be requeued.
        """
        bot_token = await self.find_bot(channel_id)
        logger.info(json.dumps(
            {
                'channel_id': channel_id,
                'message': message,
            }, indent=4, ensure_ascii=False
        ))
        retry_count = 0
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        parse_mode = 'Markdown'
        if resource == 'instagram':
            parse_mode = 'HTML'
        payload = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': parse_mode,
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(url, json=payload, proxy="http://192.168.10.53:10809") as resp:
                    response_data = await resp.json()
                    if resp.status == 200:
                        logger.info(f"Message sent successfully! Response: {json.dumps(response_data, indent=2)}")
                    else:
                        logger.error(f"Failed to send message. Status: {resp.status}, Response: {json.dumps(response_data, indent=2)}")
            self.mark_bot_used(channel_id, bot_token)
        except aiohttp.ClientConnectorError as ce:
            logger.error(f"Proxy connection error: {ce}")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"Client error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    # async def send_file(self, channel_id, file_path, caption='', pin=False):
    #     bot_token = await self.find_bot(channel_id)
    #     try:
    #         logger.info(file_path)
    #         with open(file_path, 'rb') as file:
    #             response = await self.token_to_bot[bot_token].send_document(
    #                 chat_id=channel_id,
    #                 document=file,
    #                 caption=caption,
    #             )
    #             logger.info(f"Sent file to channel {channel_id} with bot {bot_token[:10]}...")
    #             self.mark_bot_used(channel_id, bot_token)
    #             if response.message_id:
    #                 if pin:
    #                     await asyncio.sleep(3)
    #                     await self.token_to_bot[bot_token].pin_chat_message(channel_id, response.message_id)
    #                 return True, response
    #             return False, None
    #     except FileNotFoundError:
    #         logger.error(f"File not found: {file_path}")
    #         return False, None
    #     except Exception as e:
    #         logger.error(f"Error sending file: {e}")
    #         return False, None        
