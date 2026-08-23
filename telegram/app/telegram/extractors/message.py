from datetime import datetime, timezone
from telethon.tl.types import MessageReplyHeader, InputReplyToMessage
import traceback
import re

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.parsers.entities import *
from app.telegram.parsers.medias import *
from app.telegram.parsers.emojies import *

from utils.models_handler import get_sentiment, get_sense, get_category


class MessageExtractor:

    @staticmethod
    def check_persian_character(message):
        # Check to exist at least one Persian character
        has_farsi = re.search(r'[\u0600-\u06FF]', message)
        if has_farsi:
            # Remove all non persian characters
            cleaned = re.sub(r"[^\u0600-\u06FF\s]", "", message)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return cleaned if len(cleaned) > 0 else None
        else:
            return None

    @staticmethod
    def get_message_id(obj):
        return obj.id

    @staticmethod
    def get_peer_id(peer_id):
        """
        	In the context of Telegram APIs, the term "peer" and specifically "peer_id" refers to an identifier used to represent a specific entity in Telegram, such as a user, group, or channel, within the context of a particular operation or message. The peer_id is part of Telegram's API structure to uniquely identify the recipient or target of an action, such as sending a message or performing other operations.
        """
        if not peer_id:
            return None
        if isinstance(peer_id, PeerUser):
            return peer_id.user_id
        elif isinstance(peer_id, PeerChat):
            return peer_id.chat_id  # Negative integer for groups
        elif isinstance(peer_id, PeerChannel):
            return peer_id.channel_id
        else:
            return None

    @staticmethod
    def get_peer_type(peer_id):
        if not peer_id:
            return None
        if isinstance(peer_id, PeerUser):
            return 'USER'
        elif isinstance(peer_id, PeerChat):
            return 'CHAT'
        elif isinstance(peer_id, PeerChannel):
            return 'CHANNEL'
        else:
            return None

    @staticmethod
    def get_author_id(from_id):
        if not from_id:
            return None
        if isinstance(from_id, PeerUser):
            return from_id.user_id
        elif isinstance(from_id, PeerChat):
            return from_id.chat_id
        elif isinstance(from_id, PeerChannel):
            return from_id.channel_id
        else:
            return None

    @staticmethod
    def get_author_type(from_id):
        if not from_id:
            return None
        if isinstance(from_id, PeerUser):
            return 'USER'
        elif isinstance(from_id, PeerChat):
            return 'CHAT'
        elif isinstance(from_id, PeerChannel):
            return 'CHANNEL'
        else:
            return None

    @staticmethod
    def get_fwd_peer_id(obj):
        if not obj.fwd_from:
            return None
        fwd_peer_id = MessageExtractor.get_peer_id(obj.fwd_from.from_id)
        if not fwd_peer_id and obj.fwd_from.channel_post:
            return MessageExtractor.get_peer_id(obj.peer_id)
        return fwd_peer_id

    @staticmethod
    def get_fwd_peer_type(obj):
        if not obj.fwd_from:
            return None
        fwd_peer_type = MessageExtractor.get_peer_type(obj.fwd_from.from_id)
        if not fwd_peer_type and obj.fwd_from.channel_post:
            return MessageExtractor.get_peer_type(obj.peer_id)
        if not fwd_peer_type and hasattr(obj.fwd_from, 'from_name') and obj.fwd_from.from_name:
            return 'USER'
        return fwd_peer_type

    @staticmethod
    def get_fwd_link(obj):
        if not obj.fwd_from or not obj.fwd_from.channel_post:
            return None
        channel_id = MessageExtractor.get_fwd_peer_id(obj)
        return f'https://t.me/c/{channel_id}/{obj.fwd_from.channel_post}'

    @staticmethod
    def get_reply_peer_id(obj):

        if not obj.reply_to:
            return None
        reply_peer_id = None

        if isinstance(obj.reply_to, MessageReplyHeader):
            if obj.reply_to.reply_to_peer_id:
                reply_peer_id = MessageExtractor.get_peer_id(obj.reply_to.reply_to_peer_id)
            if obj.reply_to.reply_from and obj.reply_to.reply_from.from_id:
                reply_peer_id = MessageExtractor.get_peer_id(obj.reply_to.reply_from.from_id)
            if not reply_peer_id and (
                (obj.reply_to.reply_from and obj.reply_to.reply_from.channel_post)
                or obj.reply_to.reply_to_msg_id
            ):
                return MessageExtractor.get_peer_id(obj.peer_id)

        elif isinstance(obj.reply_to, InputReplyToMessage):
            return MessageExtractor.get_peer_id(obj.peer_id)

        return reply_peer_id

    @staticmethod
    def get_reply_peer_type(obj):
        if not obj.reply_to:
            return None
        reply_peer_type = None

        if isinstance(obj.reply_to, MessageReplyHeader):
            if obj.reply_to.reply_to_peer_id:
                reply_peer_type = MessageExtractor.get_peer_type(obj.reply_to.reply_to_peer_id)
            if obj.reply_to.reply_from and obj.reply_to.reply_from.from_id:
                reply_peer_type = MessageExtractor.get_peer_type(obj.reply_to.reply_from.from_id)
            if not reply_peer_type and (
                (obj.reply_to.reply_from and obj.reply_to.reply_from.channel_post)
                or obj.reply_to.reply_to_msg_id
            ):
                return MessageExtractor.get_peer_type(obj.peer_id)
            if not reply_peer_type and hasattr(obj.reply_to.reply_from, "from_name") and obj.reply_to.reply_from.from_name:
                return "USER"

        elif isinstance(obj.reply_to, InputReplyToMessage):
            # Fallback for sent messages: only peer_id available
            return MessageExtractor.get_peer_type(obj.peer_id)

        return reply_peer_type

    @staticmethod
    def get_reply_link(obj):
        if not obj.reply_to or not obj.reply_to.reply_to_msg_id:
            return None
        return f"https://t.me/c/{MessageExtractor.get_reply_peer_id(obj)}/{obj.reply_to.reply_to_msg_id}"

    @staticmethod
    def get_date(obj):
        try:
            return obj.date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None

    @staticmethod
    def get_private_url(obj):
        return f"https://t.me/c/{MessageExtractor.get_peer_id(peer_id=obj.peer_id)}/{MessageExtractor.get_message_id(obj=obj)}"

    @staticmethod
    def get_message(obj):
        message = getattr(obj, "message", None)
        if message:
            return message.strip("'").replace("'", "''")
        return message

    @staticmethod
    def get_reactions(obj):
        try:
            return [{'EMOJI': r.reaction.emoticon, 'COUNT': r.count} for r in obj.reactions.results]
        except Exception:
            return None

    @staticmethod
    def get_reactions_count(obj):
        try:
            return sum(r.count for r in obj.reactions.results)
        except Exception:
            return 0

    @staticmethod
    def get_text_reactions(obj):
        if obj.message:
            return list(set(emoji_pattern.findall(obj.message)))
        return []

    @staticmethod
    def get_replies_count(obj):
        try:
            return obj.replies.replies
        except Exception:
            return 0

    @staticmethod
    def get_edit_date(obj):
        if obj.edit_date:
            return obj.edit_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        return None

    @staticmethod
    def get_views_count(obj):
        try:
            if obj.views:
                return obj.views
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_forwards_count(obj):
        try:
            if obj.forwards:
                return obj.forwards
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_tags(message: str):
        try:
            response = get_category(message=message)
            return response.get("result", [])
        except Exception as e:
            #logger.error(
            #    " ".join(traceback.format_exception(type(e), e, e.__traceback__))
            #)
            return None

    @staticmethod
    def get_sentiment(message: str):
        try:
            response = get_sentiment(message=message)
            return response.get("result", None)
        except Exception as e:
            #logger.error(
            #    " ".join(traceback.format_exception(type(e), e, e.__traceback__))
            #)
            return None

    @staticmethod
    def get_sense(message: str):
        try:
            response = get_sense(message=message)
            return response.get("result", None)
        except Exception as e:
            #logger.error(
            #    " ".join(traceback.format_exception(type(e), e, e.__traceback__))
            #)
            return None

    @staticmethod
    def get_media(obj):
        if isinstance(obj.media, MESSAGE_GEO):
            return ['MEDIA_GEO']

        if isinstance(obj.media, MESSAGE_GIFT):
            return ['MEDIA_GIFT']

        if isinstance(obj.media, MESSAGE_PAYMENT):
            return ['MEDIA_PAYMENT']

        if isinstance(obj.media, MESSAGE_POOL):
            return ['MEDIA_POOL']

        if isinstance(obj.media, MESSAGE_MEDIAS):
            if isinstance(obj.media, MessageMediaPhoto):
                return ['MEDIA_PHOTO']
            if (
                (hasattr(obj.media, 'video') and obj.media.video) 
                    or 
                (hasattr(obj.media, 'round') and obj.media.round)
                ):
                return ['MEDIA_VIDEO']

            if hasattr(obj.media, 'document') and obj.media.document.mime_type.startswith('audio/mpeg'):
                return ['MEDIA_MUSIC']

            if hasattr(obj.media, 'document') and obj.media.document.mime_type.startswith('audio/ogg'):
                return ['MEDIA_VOICE']

            if hasattr(obj.media, 'document') and obj.media.document.mime_type.startswith('image'):
                return ['MEDIA_PHOTO']
        return None

    @staticmethod
    def utf16_offset_to_py_index(text, utf16_offset):
        """
        Converts a UTF-16 offset (used by Telegram) to a Python string index.
        """
        count = 0
        py_index = 0
        for char in text:
            utf16_len = 2 if ord(char) > 0xFFFF else 1
            if count + utf16_len > utf16_offset:
                break
            count += utf16_len
            py_index += 1
        return py_index

    @staticmethod
    def get_entities(obj):
        if not obj.entities:
            return []
        return [type(entity).__name__ for entity in obj.entities]

    @staticmethod
    def extract_entities(obj):
        text = obj.message

        entities = obj.entities or []
        to_remove = []
        message_urls = []
        # message_mention_username = []
        # message_mention_name = []
        message_mentions = []
        message_hashtag = []
        # message_email = []
        message_code_sections = []

        bolded_parts = []
        # italic_parts = []
        strikethroughed_parts = []
        monospace_parts = []
        spoiler_parts = []
        blockquote_parts = []

        for entity in entities:
            start = MessageExtractor.utf16_offset_to_py_index(text, entity.offset)
            end = MessageExtractor.utf16_offset_to_py_index(
                text, entity.offset + entity.length
            )
            entity_text = text[start:end]

            if isinstance(entity, REMOVE_TYPES):
                to_remove.append((start, end))

            elif isinstance(entity, DUPLICATE_TYPES):
                if isinstance(entity, MessageEntityEmail):
                    # message_email.append(entity_text)
                    message_urls.append(entity_text)
                if isinstance(entity, MessageEntityMentionName):
                    # message_mention_name.append(entity_text)
                    message_mentions.append(entity_text)
                if isinstance(entity, MessageEntityMention):
                    # message_mention_username.append(entity_text)
                    message_mentions.append(entity_text)
                if isinstance(entity, MessageEntityUrl):
                    message_urls.append(entity_text)
                if isinstance(entity, MessageEntityPre):
                    message_code_sections.append(entity_text)

                to_remove.append((start, end))

            elif isinstance(entity, KEEP_TYPES):
                if (
                    isinstance(entity, MessageEntityBold)
                    and entity_text.replace(" ", "") != ""
                ):
                    bolded_parts.append(entity_text)
                # if isinstance(entity, MessageEntityItalic) and entity_text.replace(" ", "")!="":
                #     italic_parts.append(entity_text)
                if (
                    isinstance(entity, MessageEntitySpoiler)
                    and entity_text.replace(" ", "") != ""
                ):
                    spoiler_parts.append(entity_text)
                if isinstance(entity, MessageEntityHashtag):
                    message_hashtag.append(entity_text)
                if isinstance(entity, MessageEntityTextUrl):
                    message_urls.append(entity.url)
                if (
                    isinstance(entity, MessageEntityStrike)
                    and entity_text.replace(" ", "") != ""
                ):
                    strikethroughed_parts.append(entity_text)
                if (
                    isinstance(entity, MessageEntityCode)
                    and entity_text.replace(" ", "") != ""
                ):
                    monospace_parts.append(entity_text)
                if (
                    isinstance(entity, MessageEntityBlockquote)
                    and entity_text.replace(" ", "") != ""
                ):
                    blockquote_parts.append(entity_text)

        # Remove segments in reverse order to avoid offset shifting
        for start, end in sorted(to_remove, reverse=True):
            text = text[:start] + text[end:]

        return {
            "CLEANED_MESSAGE": text,
            "LINKS": message_urls,
            "MENTIONS": message_mentions,
            "HASHTAGS": message_hashtag,
            "BOLDED_PARTS": list(set(bolded_parts)),
            # 'ITALIC_PARTS': list(set(italic_parts)),
            "STRIKETHROUGHT_PARTS": list(set(strikethroughed_parts)),
            "MONOSPACE_PARTS": list(set(monospace_parts)),
            "SPOILER_PARTS": list(set(spoiler_parts)),
            "BLOCKQUOTE_PARTS": list(set(blockquote_parts)),
            "CODES": message_code_sections,
        }
