"""
Pydantic Schemas Package
"""
from .base import BaseSchema
from .users import User, UserCreate, UserUpdate
from .telegram_peers import TelegramPeer, TelegramPeerCreate, TelegramPeerUpdate
from .telegram_channels import TelegramChannel, TelegramChannelCreate, TelegramChannelUpdate
from .user_queries import UserQueries, UserQueriesCreate, UserQueriesUpdate
from .telegram_accounts import TelegramAccount, TelegramAccountCreate, TelegramAccountUpdate
from .rss_resources import RSSResource, RSSResourceCreate, RSSResourceUpdate
from .telegram_channels_underfollow import (
    TelegramChannelsUnderFollow, 
    TelegramChannelsUnderFollowCreate, 
    TelegramChannelsUnderFollowUpdate
)
from .telegram_users_underfollow import (
    TelegramUsersUnderFollow, 
    TelegramUsersUnderFollowCreate, 
    TelegramUsersUnderFollowUpdate
)

__all__ = [
    "BaseSchema",
    "User", "UserCreate", "UserUpdate",
    "TelegramPeer", "TelegramPeerCreate", "TelegramPeerUpdate",
    "TelegramChannel", "TelegramChannelCreate", "TelegramChannelUpdate",
    "UserQueries", "UserQueriesCreate", "UserQueriesUpdate",
    "TelegramAccount", "TelegramAccountCreate", "TelegramAccountUpdate",
    "RSSResource", "RSSResourceCreate", "RSSResourceUpdate",
    "TelegramChannelsUnderFollow", "TelegramChannelsUnderFollowCreate", "TelegramChannelsUnderFollowUpdate",
    "TelegramUsersUnderFollow", "TelegramUsersUnderFollowCreate", "TelegramUsersUnderFollowUpdate",
] 