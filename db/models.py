import enum
from datetime import datetime, UTC
import sqlalchemy as sql
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from database import Base
import database as db


class UserQueries(Base):
    __tablename__ = "user_queries"
    id = sql.Column(sql.BigInteger, primary_key=True, index=True)

    title = sql.Column(sql.String(100), nullable=False, default="")
    description = sql.Column(sql.String(100), nullable=False, default="")
    query_type = sql.Column(sql.BigInteger, nullable=False, default=0, index=True)
    must = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
    should = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
    must_not = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
    query_string = sql.Column(sql.String(1000), nullable=True, default="")


# class UserChannels(Base):
#     __tablename__ = "user_channels"

#     id = sql.Column(sql.BigInteger, primary_key=True, index=True)
#     chat_id = sql.Column(sql.BigInteger, unique=True, nullable=False, index=True)
#     interval = sql.Column(sql.String(32), nullable=False, index=True, default='1d')
#     bot_tokens = sql.Column(ARRAY(sql.String(100)), nullable=True)
#     disabled = sql.Column(sql.Boolean, default=False)

#     user_id = sql.Column(sql.BigInteger, ForeignKey("users.id"), nullable=False, index=True)
#     user = relationship("User", back_populates="channels")

#     query_id = sql.Column(sql.BigInteger, ForeignKey("user_queries.id"), nullable=False, index=True)
#     query = relationship("UserQueries", back_populates="channel")


# class UserQueryIds(Base):
#     __tablename__ = "user_query_ids"
#     id = sql.Column(sql.BigInteger, primary_key=True, index=True)
#     title = sql.Column(sql.String(100), nullable=False, default="")
#     description = sql.Column(sql.String(100), nullable=False, default="")
#     query_type = sql.Column(sql.BigInteger, nullable=False, default=0, index=True)
#     must = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
#     should = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
#     must_not = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
#     query_string = sql.Column(sql.String(1000), nullable=True, default="")


class User(Base):
    __tablename__ = "users"

    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    username = sql.Column(sql.String(32), unique=True, nullable=False, index=True)
    full_name = sql.Column(sql.String(32), unique=False, nullable=False)
    email = sql.Column(sql.String(100), unique=True, index=True, nullable=False)
    hashed_password = sql.Column(sql.String(100), nullable=False)
    disabled = sql.Column(sql.Boolean, default=False)
    permissions = sql.Column(ARRAY(sql.String(100)), nullable=False, default=list)
    history = sql.Column(ARRAY(JSONB), nullable=False, default=list)
    query_ids = sql.Column(ARRAY(sql.BigInteger), default=[i for i in range(1, 60)])

    following_channels = sql.Column(ARRAY(sql.BigInteger), default=[])
    following_groups = sql.Column(ARRAY(sql.BigInteger), default=[])
    following_users = sql.Column(ARRAY(sql.BigInteger), default=[])

    accessible_urls = sql.Column(ARRAY(sql.String(100)), default=[])


class TelegramChannel(Base):
    __tablename__ = "telegram_channels"

    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    key = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
    value = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
    tag = sql.Column(sql.String(50), index=True, nullable=True, default=None)
    chat_id = sql.Column(sql.BigInteger, index=True, nullable=True, default=None)
    access_hash = sql.Column(sql.BigInteger, index=True, nullable=True, default=None)
    in_progress = sql.Column(sql.Boolean, default=False)
    blocked = sql.Column(sql.Boolean, default=False)
    last_update = sql.Column(sql.DateTime, index=True, default=lambda: datetime.now(UTC))
    subscribed_by = sql.Column(sql.BigInteger, index=True, nullable=True, default=None)

    # Relationship to TelegramChannelsUnderFollow
    under_follow = relationship("TelegramChannelsUnderFollow", back_populates="channel")


class TelegramPeer(Base):
    __tablename__ = "telegram_peers"

    id = sql.Column(sql.BigInteger, primary_key=True, autoincrement=True)
    username = sql.Column(sql.String(100), index=True, nullable=True, default=None)
    url = sql.Column(sql.String(100), index=True, nullable=True, default=None)
    peer_id = sql.Column(sql.BigInteger, unique=True, index=True, nullable=True, default=None)
    blocked = sql.Column(sql.Boolean, default=False)
    linked_peer_id = sql.Column(sql.BigInteger, index=True, nullable=True, default=None)
    subscriber = sql.Column(sql.BigInteger, index=True, nullable=True, default=None)
    is_channel = sql.Column(sql.Boolean, nullable=True, default=None)
    on_waiting = sql.Column(sql.Boolean, default=False)

class TelegramChannelsUnderFollow(Base):
    __tablename__ = "telegram_channels_under_follow"

    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    channel_id = sql.Column(sql.BigInteger, ForeignKey("telegram_channels.id"), nullable=False, index=True)
    added_at = sql.Column(sql.DateTime, index=True, default=lambda: datetime.now(UTC))
    is_active = sql.Column(sql.Boolean, default=True)
    priority = sql.Column(sql.Integer, default=0)
    notes = sql.Column(sql.String(500), nullable=True, default=None)
    
    # Relationship to access all TelegramChannel details
    channel = relationship("TelegramChannel", back_populates="under_follow")


class TelegramUsersUnderFollow(Base):
    __tablename__ = "telegram_users_under_follow"
    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    user_id = sql.Column(sql.BigInteger, unique=True, nullable=False, index=True)
    username = sql.Column(sql.String(100), nullable=True, default=None)
    added_at = sql.Column(sql.DateTime, index=True, default=lambda: datetime.now(UTC))
    is_active = sql.Column(sql.Boolean, default=True)
    priority = sql.Column(sql.Integer, default=0)
    notes = sql.Column(sql.String(500), nullable=True, default=None)


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    phone = sql.Column(sql.BigInteger, index=True, nullable=False, unique=True)
    api_id = sql.Column(sql.BigInteger, index=True, nullable=False)
    api_hash = sql.Column(sql.String(100), index=True, nullable=False)
    session_file = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
    process = sql.Column(sql.Integer, nullable=False, default=0)
    roles = sql.Column(ARRAY(sql.String(50)), default=[])


class RSSResource(Base):
    __tablename__ = "rss_resources"
    
    id = sql.Column(sql.BigInteger, primary_key=True, index=True)
    key = sql.Column(sql.String(100), index=True, unique=True, nullable=False)
    value_rss = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
    blocked = sql.Column(sql.Boolean, default=False)
    last_update = sql.Column(sql.DateTime, index=True, default=lambda: datetime.now(UTC))


# class TwitterChannel(Base):
#     __tablename__ = "twitter_pages"
    
#     id = sql.Column(sql.BigInteger, primary_key=True, index=True)
#     key = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
#     value = sql.Column(sql.String(100), index=True, nullable=False, unique=True)
#     tag = sql.Column(sql.String(50), index=True, nullable=True, default=None)
#     in_progress = sql.Column(sql.Boolean, default=False)
#     blocked = sql.Column(sql.Boolean, default=False)
#     last_update = sql.Column(sql.DateTime, index=True, default=lambda: datetime.now(UTC))
