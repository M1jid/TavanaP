from telethon.tl.types import ChatFull, Channel
from telethon.tl.types import messages

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import traceback

from telethon.tl.types import (
    ChatReactionsSome,
    ChatReactionsAll,
    ReactionEmoji,
    ReactionCustomEmoji,
)

from utils.models_handler import get_category


class PeerChannelExtractor:
    AVAILABLE_CHANNEL_REACTIONS = [
        "❤️", "🙏", "🥰", "💔", "🔥", "🤨", "🐳", "😁", "🤯", "😢", "👍",
        "👎", "🌚", "🤝", "👏", "🤔", "😱", "🤬", "🤩", "🤮", "💩", "👌",
        "🕊", "🤡", "☃️", "👀", "👨‍💻", "👻", "😭", "🤓", "🎃", "🆒", "💘",
        "😘", "🙉", "😎", "🤷‍♂️", "🤷", "🤷‍♀️", "😡", "👾", "🎅", "😐", "🍓",
        "💋", "🖕", "😈", "😴", "🍌", "🏆", "💊", "🦄", "🙈", "🗿", "🤪",
        "💅", "🥱", "🥴", "😍", "🌭", "💯", "🤣", "⚡️", "🫡", "😨", "✍️",
        "🤗", "❤️‍🔥", "🎉", "😇", "🍾", "🎄",
    ]

    @staticmethod
    def get_id(obj):
        if isinstance(obj, messages.ChatFull):
            return obj.full_chat.id
        if isinstance(obj, Channel):
            return obj.id

    @staticmethod
    def get_username(obj):
        chat = None
        if isinstance(obj, messages.ChatFull):
            chat = obj.chats[0]
        if isinstance(obj, Channel):
            chat = obj

        if chat.username:
            return chat.username

        if chat.usernames:
            for item in chat.usernames:
                if item.active:
                    return item.username
        return None

    @staticmethod
    def get_can_view_participants(obj):
        if isinstance(obj, messages.ChatFull):
            return obj.full_chat.can_view_participants
        return None

    @staticmethod
    def get_description(obj):
        if isinstance(obj, messages.ChatFull):
            return obj.full_chat.about.strip("'").replace("'", "''")
        return None

    @staticmethod
    def get_participants_count(obj):
        if isinstance(obj, messages.ChatFull):
            return int(obj.full_chat.participants_count)
        return None

    @staticmethod
    def get_title(obj):
        if isinstance(obj, messages.ChatFull):
            return obj.chats[0].title.strip("'").replace("'", "''")
        if isinstance(obj, Channel):
            return obj.title
    
    @staticmethod
    def get_available_reactions(obj):
        available_reactions = []
        if (
            isinstance(obj, messages.ChatFull)
            and hasattr(obj.full_chat, "available_reactions")
            and obj.full_chat.available_reactions
        ):
            if isinstance(obj.full_chat.available_reactions, ChatReactionsSome):
                for reaction in obj.full_chat.available_reactions.reactions:
                    if isinstance(reaction, ReactionEmoji):
                        available_reactions.append(reaction.emoticon)
                    elif isinstance(reaction, ReactionCustomEmoji):
                        # fallback: store ID or some placeholder
                        available_reactions.append(f"[custom:{reaction.document_id}]")
            elif isinstance(obj.full_chat.available_reactions, ChatReactionsAll):
                return PeerChannelExtractor.AVAILABLE_CHANNEL_REACTIONS
        return available_reactions

    @staticmethod
    def get_url(obj):
        username = PeerChannelExtractor.get_username(obj=obj)
        if username:
            return f'https://t.me/{username}'
        return f"https://t.me/c/{PeerChannelExtractor.get_id(obj=obj)}"

    @staticmethod
    def get_linked_chat_id(obj):
        if isinstance(obj, messages.ChatFull):
            return obj.full_chat.linked_chat_id

    @staticmethod
    def get_linked_chat_title(obj):
        if isinstance(obj, messages.ChatFull):
            if len(obj.chats) > 1:
                return obj.chats[1].title.strip("'").replace("'", "''")
        return None

    @staticmethod
    def get_linked_chat_username(obj):
        if isinstance(obj, messages.ChatFull):
            if len(obj.chats) > 1:
                chat = obj.chats[1]

                if chat.username:
                    return chat.username

                if chat.usernames:
                    for item in chat.usernames:
                        if item.active:
                            return item.username
        return None

    @staticmethod
    def get_tag(obj):
        about = PeerChannelExtractor.get_description(obj=obj)
        try:
            # response = get_category(message=about)
            # return response.get("result", [])
            return []
        except Exception as e:
            # logger.error(
            #     " ".join(traceback.format_exception(type(e), e, e.__traceback__))
            # )
            return []
