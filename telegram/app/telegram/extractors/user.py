from telethon.tl.types.users import UserFull
from telethon.tl.types import User

from datetime import datetime, timezone
import time

# Logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserExtractor:

    @staticmethod
    def get_type(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        if user.bot:
            return "BOT"
        return "USER"

    @staticmethod
    def get_id(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        return user.id

    @staticmethod
    def get_bio(obj):
        if isinstance(obj, UserFull) and obj.full_user.about:
            return obj.full_user.about.strip("'").replace("'", "''")
        return None

    @staticmethod
    def get_first_name(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        if user.first_name:
            return user.first_name.strip("'").replace("'", "''")
        return None

    @staticmethod
    def get_last_name(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        if user.last_name:
            return user.last_name.strip("'").replace("'", "''")
        return None


    @staticmethod
    def get_phone(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        if user.phone:
            return user.phone
        return None

    @staticmethod
    def get_username(obj):
        user = None
        if isinstance(obj, UserFull):
            user = obj.users[0]
        elif isinstance(obj, User):
            user = obj
        else:
            return None

        if user.username:
            return user.username

        if user.usernames:
            for item in user.usernames:
                if item.active:
                    return item.username
        return None

    @staticmethod
    def get_private_forward_name(obj):
        if isinstance(obj, UserFull):
            if obj.full_user and obj.full_user.private_forward_name:
                return obj.full_user.private_forward_name.strip("'").replace("'", "''")
        return None

    @staticmethod
    def get_birthday(obj):
        return None
        if isinstance(obj, UserFull) and obj.full_user.birthday:
            return obj.full_user.birthday.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        return None

    @staticmethod
    def get_personal_channel_id(obj):
        if isinstance(obj, UserFull) and obj.full_user.personal_channel_id:
            return obj.full_user.personal_channel_id
        return None

    @staticmethod
    def get_personal_channel_title(obj):
        if isinstance(obj, UserFull):
            if obj.chats and obj.chats[0].title:
                return obj.chats[0].title.strip("'").replace("'", "''")
        return None

    @staticmethod
    def extract(obj):
        return {
            "FETCH_TIME": int(time.time()),
            "TYPE": UserExtractor.get_type(obj=obj),
            "ID": str(UserExtractor.get_id(obj=obj)),
            "USER_ID": UserExtractor.get_id(obj=obj),
            "BIO": UserExtractor.get_bio(obj=obj),
            "FIRST_NAME": UserExtractor.get_first_name(obj=obj),
            "LAST_NAME": UserExtractor.get_last_name(obj=obj),
            "PHONE": UserExtractor.get_phone(obj=obj),
            "USERNAME": UserExtractor.get_username(obj=obj),
            "PRIVATE_FORWARD_NAME": UserExtractor.get_private_forward_name(obj=obj),
            "BIRTHDAY": UserExtractor.get_birthday(obj=obj),
            "PERSONAL_CHANNEL_ID": UserExtractor.get_personal_channel_id(obj=obj),
            "PERSONAL_CHANNEL_TITLE": UserExtractor.get_personal_channel_title(obj=obj),
        }
