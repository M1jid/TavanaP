# telethon
import telethon
from telethon.sync import events
from telethon.tl.types import Channel
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.types import PeerChannel
from telethon.tl.types import PeerUser
from telethon.tl.types import User
from telethon.tl.functions.messages import GetDiscussionMessageRequest

# Additions
import os
import asyncio
import random
import base64
import tempfile
import time
from typing import List
from datetime import datetime, timezone, timedelta

# Config
from app.core.config import settings

from app.telegram.extractors.channel import ChannelExtractor
from app.telegram.extractors.group import GroupExtractor
from app.telegram.extractors.user import UserExtractor

# Extractors
from app.telegram.extractors.peer_channel import PeerChannelExtractor
from app.telegram.extractors.message import MessageExtractor
from app.telegram.extractors.channel_message import ChannelMessageExtractor
from app.telegram.extractors.channel_comment import ChannelCommentExtractor
from app.telegram.extractors.group_message import GroupMessageExtractor
from app.telegram.extractors.chat_message import ChatMessageExtractor

# Decorators, exceptions and services
from app.telegram.decorators import retry_on_proxy_error_async
from app.telegram import exceptions as telegram_exceptions
from app.services import telegram_peer as peer_service
from app.services import entity_range_service, message_router_service

from app.schemas.telegram_account import TelegramSchemaResponseAccount

# handlers
from app.startup import (
    elastic_handler,
    ksql_handler,
    minio_handler,
    redis_handler,
    proxy_server,
)

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(
        self,
        account: TelegramSchemaResponseAccount,
    ) -> None:

        self.account_api_id = account.api_id
        self.account_api_hash = account.api_hash
        self.account_phone = account.phone
        self.account_account_id = account.id
        self.account_session_path = f'metadata/sessions/{account.session_file}'
        self.account_roles = account.roles

        # Channels data
        self.channel_id_to_top_message = {} # Maps every channel id to its last message id
        self.channel_id_to_entity = {} # Maps every channel id to its entity
        self.channel_ids = [] # List of available channel ids
        self.channel_id_to_linked_group = {}

        # Groups data
        self.group_id_to_top_message = {} # Maps every group id to its last message id
        self.group_id_to_entity = {} # Maps every group id to its entity
        self.group_ids = [] # List of available group ids
        self.group_id_to_linked_channel = {}
        self.forwarded_messages_to_discussion = {}

        # Users data
        self.user_id_to_entity = {} # Maps every user id to its entity
        self.user_ids = [] # List of available user ids

        self.new_chat_messages_to_fetch = {}

        self.client_entity = None

        # Telegram client instance
        self.client = telethon.sync.TelegramClient(
            self.account_session_path,
            self.account_api_id,
            self.account_api_hash,
            proxy=proxy_server,
        )
    
    def free_channels(self):
        peer_service.unsubscribe_but_joinable_by_phone(subscriber=self.account_phone)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def start_client(self):
        # try:
        await self.client.start(phone=self.account_phone)
        self.session = await self.client(telethon.tl.functions.account.GetAuthorizationsRequest())
        if not await self.client.is_user_authorized():
            await self.client.connect()
        logger.info('Loggin')
        # except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
        #     logger.error('PhoneNumberBannedError')
        #     self.free_channels()
        # except telethon.errors.rpcerrorlist.AuthKeyDuplicatedError:
        #     logger.error('AuthKeyDuplicatedError')
        #     self.free_channels()
        # except telethon.errors.PhoneNumberInvalidError:
        #     # self.free_channels()
        #     logger.error('PhoneNumberInvalidError')
        # except telethon.errors.PhoneCodeInvalidError:
        #     self.free_channels()
        #     logger.error('PhoneCodeInvalidError')
        # except telethon.errors.PhoneCodeExpiredError:
        #     logger.error('PhoneCodeExpiredError')
        # except telethon.errors.SessionPasswordNeededError:
        #     logger.error('SessionPasswordNeededError')
        # except telethon.errors.PasswordHashInvalidError:
        #     logger.error('PasswordHashInvalidError')
        # except telethon.errors.SessionRevokedError:
        #     self.free_channels()
        #     logger.error('SessionRevokedError')
        # except telethon.errors.AuthKeyDuplicatedError:
        #     self.free_channels()
        #     logger.error('AuthKeyDuplicatedError')
        # except telethon.errors.AuthKeyUnregisteredError:
        #     self.free_channels()
        #     logger.error('AuthKeyUnregisteredError')
        # except telethon.errors.UserDeactivatedBanError:
        #     self.free_channels()
        #     logger.error('UserDeactivatedBanError')
        # except telethon.errors.UserDeactivatedError:
        #     self.free_channels()
        #     logger.error('UserDeactivatedError')
        # except Exception as e:
        #     raise e

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def fetch_entity_by_link(self, link):
        return await self.client.get_entity(link)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def fetch_entity_by_id(self, target_id): 
        try: 
            return await self.client.get_entity(target_id) 
        except (telethon.errors.ChannelPrivateError, telethon.errors.ChannelInvalidError):
            return None
        except ValueError:
            return None

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def fetch_full_channel(self, entity):
        channel_full = await self.client(GetFullChannelRequest(channel=entity))
        await asyncio.sleep(3)
        return channel_full

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def fetch_user(self, user_id):
        user_full = await self.client(GetFullUserRequest(PeerUser(user_id)))
        await asyncio.sleep(3)
        return user_full

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def fetch_full_user(self, user_id):
        try:
            return await self.client(GetFullUserRequest(id=user_id))
        except ValueError as e:
            logger.error(f"Could not find user {user_id}: {str(e)}")
            return None

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def get_last_message_id(self, chat_id):
        result = await self.client(telethon.functions.messages.GetPeerDialogsRequest(peers=[chat_id]))
        return result.dialogs[0].top_message

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def left_from_channel(self, channel_id):
        channel = PeerChannel(channel_id)
        await self.client(LeaveChannelRequest(channel))

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def get_discuttion_details(self, entity, message_id):
        try:
            return await self.client(GetDiscussionMessageRequest(peer=entity, msg_id=message_id))
        except telethon.errors.rpcerrorlist.MsgIdInvalidError:
            return None
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def download_profile_photo(self, entity, channel_id, bucket_name: str = None):
        await self.client.download_profile_photo(entity, f'{channel_id}.jpg', download_big=False)
        minio_handler.upload_file(file_path=f'{channel_id}.jpg', object_name=f'{channel_id}.jpg', bucket_name=bucket_name)
        await asyncio.sleep(3)
        try:
            os.remove(f'{channel_id}.jpg')
        except Exception:
            logger.error(f'User has no profile photo')

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def download_media(self, media, file_path):
        file_path = await self.client.download_media(media, file=file_path)
        minio_handler.upload_file(file_path=file_path, object_name=file_path, bucket_name=settings.MINIO_TELEGRAM_MEDIA_CHATS_BUCKET_NAME)
        await asyncio.sleep(3)
        try:
            os.remove(file_path)
            return file_path
        except Exception:
            logger.error(f'Media {file_path} not found')

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def register_the_event_handler(self):
        self.client.on(events.NewMessage(outgoing=True, incoming=True))(self.handle_new_message)
        # self.client.on(events.NewMessage)(self.handle_new_message)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def get_entity_creation_date(self, entity):
        messages = await self.client.get_messages(entity, limit=1, reverse=True)
        if messages:
            return messages[0].date
        return None

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _store_group_details(self, entity_id, entity=None, entity_doc=None):
        if not entity:
            entity = await self.fetch_entity_by_id(target_id=entity_id)
        if not entity:
            return
        channel_full = await self.fetch_full_channel(entity=entity)
        draft = GroupExtractor.extract(obj=channel_full)
        draft['FOLLOWERS'] = [{'FOLLOWERS': draft['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
        if entity_doc:
            draft['FOLLOWERS'].extend(entity_doc['FOLLOWERS'])
            await elastic_handler.update_document(index_name=settings.TEGRAM_GROUPS_TOPIC_NAME, document_id=entity_id, update_data=draft)
        else:
            draft['CREATION_DATE'] = await self.get_entity_creation_date(entity=entity)
            await elastic_handler.index_document(index_name=settings.TEGRAM_GROUPS_TOPIC_NAME, document_id=entity_id, document=draft)
        await self.sync_entity_to_database(entity=entity, linked_peer_id=draft['LINKED_CHANNEL_ID'], _type=False)
        await self.download_profile_photo(entity=entity, channel_id=entity.id, bucket_name=settings.MINIO_TELEGRAM_GROUP_BUCKET_NAME)
        await asyncio.sleep(3)
        return channel_full

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _store_channel_details(self, entity_id, entity=None, entity_doc=None):
        if not entity:
            entity = await self.fetch_entity_by_id(target_id=entity_id)
        if not entity:
            return
        channel_full = await self.fetch_full_channel(entity=entity)
        draft = ChannelExtractor.extract(obj=channel_full)
        draft['FOLLOWERS'] = [{'FOLLOWERS': draft['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
        if entity_doc:
            draft['FOLLOWERS'].extend(entity_doc['FOLLOWERS'])
            await elastic_handler.update_document(index_name=settings.TEGRAM_CHANNELS_TOPIC_NAME, document_id=entity_id, update_data=draft)
        else:
            draft['CREATION_DATE'] = await self.get_entity_creation_date(entity=entity)
            await elastic_handler.index_document(index_name=settings.TEGRAM_CHANNELS_TOPIC_NAME, document_id=entity_id, document=draft)
        await self.sync_entity_to_database(entity=entity, linked_peer_id=draft['LINKED_GROUP_ID'], _type=True)
        await self.download_profile_photo(entity=entity, channel_id=entity.id, bucket_name=settings.MINIO_TELEGRAM_CHANNEL_BUCKET_NAME)
        await self.get_similar_channels(entity=entity)
        await asyncio.sleep(3)
        return channel_full

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _store_user_details(self, user_id, full_user, entity_doc=None):
        if not full_user:
            full_user = await self.fetch_full_user(user_id=user_id)
        if not full_user:
            return
        if full_user:
            draft = UserExtractor.extract(obj=full_user)
            if entity_doc:
                await elastic_handler.update_document(index_name=settings.TELEGRAM_USERS_TOPIC_NAME, document_id=user_id, update_data=draft)
            else:
                await elastic_handler.index_document(index_name=settings.TELEGRAM_USERS_TOPIC_NAME, document_id=user_id, document=draft)
            await self.download_profile_photo(entity=full_user.users[0], channel_id=user_id, bucket_name=settings.MINIO_TELEGRAM_USER_BUCKET_NAME)
            await asyncio.sleep(3)
            return draft
        else:
            logger.error(f'User {user_id} not found')
            return None

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def store_entity_details(self, entity_id, is_user=False):
        if is_user:
            # Test user index
            entity_doc = await elastic_handler.get_document_by_id(index_name=settings.TELEGRAM_USERS_TOPIC_NAME, document_id=entity_id)
            if entity_doc and 'FETCH_TIME' in entity_doc and entity_doc['FETCH_TIME']  > int(time.time()) - (30*24*60*60):
                return
            full_user = await self.fetch_full_user(user_id=entity_id)
            await self._store_user_details(user_id=entity_id, full_user=full_user, entity_doc=entity_doc)
        else:
            # Test channels index
            channel_entity_doc = await elastic_handler.get_document_by_id(index_name=settings.TELEGRAM_CHANNELS_TOPIC_NAME, document_id=entity_id)
            if channel_entity_doc and 'FETCH_TIME' in channel_entity_doc and channel_entity_doc['FETCH_TIME']  > int(time.time()) - (15*24*60*60):
                return

            # Test group index
            group_entity_doc = await elastic_handler.get_document_by_id(index_name=settings.TELEGRAM_GROUPS_TOPIC_NAME, document_id=entity_id)
            if group_entity_doc and 'FETCH_TIME' in group_entity_doc and group_entity_doc['FETCH_TIME']  > int(time.time()) - (15*24*60*60):
                return

            entity = await self.fetch_entity_by_id(target_id=entity_id)
            if entity:
                if isinstance(entity, Channel) and not (entity.megagroup or entity.gigagroup):
                    await self._store_channel_details(entity_id=entity_id, entity=entity, entity_doc=channel_entity_doc)
                if isinstance(entity, Channel) and (entity.megagroup or entity.gigagroup):
                    await self._store_group_details(entity_id=entity_id, entity=entity, entity_doc=group_entity_doc)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def join_to_public(self, link):
        try:
            if link:
                invite_hash = link.split('/')[3]
                updates = await self.client(telethon.tl.functions.channels.JoinChannelRequest(invite_hash))
                return updates
        except Exception:
            raise
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def join_to_private(self, invite_link: str):
        try:
            invite_hash = invite_link.split("+")[-1]
            updates = await self.client(ImportChatInviteRequest(invite_hash))
            return updates
        except Exception:
            raise
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def get_similar_channels(self, entity, MIN_NUMBERS=300):
        recommendations = await self.client(telethon.functions.channels.GetChannelRecommendationsRequest(channel=entity))
        if recommendations.chats:
            for chat in recommendations.chats:
                if chat.username and chat.username != 'None':
                    if chat.participants_count < MIN_NUMBERS:
                        logger.warning(f"Skipp https://t.me/{chat.username}. (Members: {chat.participants_count} < {MIN_NUMBERS})")
                        continue
                    await self.sync_entity_to_database(entity=chat, linked_peer_id=None, _type=True)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def handle_small_channel_leave(self, entity):
        if entity.participants_count < 100:
            logger.info(f' Left from channel {entity.id} because it has less than 100 participants')
            await self.left_from_channel(channel_id=entity.id)
            try:
                peer_service.unsubscribe_but_joinable_by_peer_id(peer_id=entity.id)
                return True
            except Exception:
                return False
        return False

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def join_new_entity(self, peer):

        if len(self.channel_ids)>=500:
            raise telegram_exceptions.CustomChannelsTooMuchError("Account Already touch maximum joined channel")

        if not peer['url'] and peer['is_channel']:
            peer_service.block_peer(peer_id=peer.id)
            logger.error(f"Failed to join to private channel using invite link: {peer['url']}")
            return

        if not peer['url'] and not peer['is_channel'] and not peer['linked_peer_id']:
            peer_service.block_peer(peer_id=peer.id)
            logger.error(f"Failed to join to linked discussion group, linked_channel not found: {peer['linked_peer_id']}")
            return

        logger.info(f"Channel: {peer}")

        if peer['url'] and '+' in peer['url']:
            try:
                result = await self.join_to_private(peer['url'])
                if not result:
                    logger.error(f"Failed to join to private channel using invite link: {peer['url']}")
                    peer_service.block_peer(peer_id=peer.id)
                    return
                else:
                    entity = result.chats[0]
                    full_channel = await self.fetch_full_channel(entity=entity)
                    await asyncio.sleep(3)
                    return await self.ensure_entity_mapping(entity=entity, full_channel=full_channel, peer=peer)
            except (telethon.errors.rpcerrorlist.InviteHashExpiredError, ValueError) as e:
                peer_service.block_peer(peer_id=peer.id)
                logger.error(f"Failed to join to private channel using invite link: {peer['url']}")
                return
            except (telethon.errors.rpcerrorlist.UserAlreadyParticipantError, ValueError) as e:
                logger.info(f"Already participant: {e}")
            return

        if peer['url'] and '+' not in peer['url']:
            try:
                result = await self.join_to_public(peer['url'])
                if not result:
                    peer_service.block_peer(peer_id=peer.id)
                    logger.error(f"Failed to join to public channel using url: {peer['url']}")
                    return
                else:
                    entity = result.chats[0]
                    full_channel = await self.fetch_full_channel(entity=entity)
                    await self.ensure_entity_mapping(entity=entity, full_channel=full_channel, peer=peer)
                    return entity
            except (telethon.errors.rpcerrorlist.UsernameNotOccupiedError, ValueError) as e:
                peer_service.block_peer(peer_id=peer.id)
                logger.error(f"Failed to join to public channel using url: {peer['url']}")
                return
            except (telethon.errors.rpcerrorlist.UserAlreadyParticipantError, ValueError) as e:
                logger.info(f"Already participant: {e}")
                return

        if not peer['url'] and not peer['is_channel'] and peer['linked_peer_id']:
            linked_channel = peer_service.get_peer_by_peer_id(peer_id=peer.linked_peer_id)
            if not linked_channel:
                peer_service.block_peer(peer_id=peer.id)
                logger.error(f"Failed to join to linked discussion group, linked_channel not found: {peer['linked_peer_id']}")
                return

            entity = await self.fetch_entity_by_id(target_id=linked_channel['peer_id'])
            if not entity:
                return
            full_channel = await self.fetch_full_channel(entity=entity)
            discussion_chat = full_channel.chats[1]
            full_discussion_chat = await self.fetch_full_channel(entity=discussion_chat)
            entity_document = await elastic_handler.get_document_by_id(index_name=settings.TELEGRAM_GROUPS_TOPIC_NAME, document_id=discussion_chat.id)
            if entity_document and 'FETCH_TIME' in entity_document and entity_document['FETCH_TIME'] < time.time() - (15*24*60*60): # 15 days
                entity_document['FOLLOWERS'] = [{'FOLLOWERS': entity_document['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
                await elastic_handler.update_document(index_name=settings.TELEGRAM_GROUPS_TOPIC_NAME, document_id=discussion_chat.id, update_data=entity_document)
            else:
                entity_document['FOLLOWERS'] = [{'FOLLOWERS': entity_document['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
                await elastic_handler.index_document(index_name=settings.TELEGRAM_GROUPS_TOPIC_NAME, document_id=discussion_chat.id, document=entity_document)

            if PeerChannelExtractor.get_participants_count(full_discussion_chat) < 0:
                logger.warning(f'Linked discussion group {discussion_chat.id} has less than 30 participants, skipping')
                peer_service.block_peer(peer_id=peer.id)
                peer_service.unsubscribe_peer(peer_id=peer.id)
                return
            try:
                result = await self.client(telethon.tl.functions.channels.JoinChannelRequest(channel=discussion_chat))
                logger.info(f"Result: {result}")
                if not result:
                    peer_service.block_peer(peer_id=peer.id)
                    logger.error(f"Failed to join to linked discussion group: {discussion_chat.id}")
                    return
                else:
                    entity = result.chats[0]
                    return await self.ensure_entity_mapping(entity=entity, unread_count=None, full_channel=full_discussion_chat, peer=peer)
            except telethon.errors.rpcerrorlist.InviteRequestSentError as join_error:
                logger.info(f'Successfully requested to join linked discussion group: {discussion_chat.id}: {join_error}')
                peer_service.wait_for_peer(peer_id=peer.id)
                return

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def ensure_entity_mapping(self, entity, last_message_id=None, unread_count=None, full_channel=None, on_startup=False, peer=None):
        if not entity or not getattr(entity, 'id', None):
            return

        if last_message_id is None:
            last_message_id = await self.get_last_message_id(chat_id=entity.id)

        if isinstance(entity, Channel) and not (entity.megagroup or entity.gigagroup):
            if full_channel is None:
                logger.info(f'Fetching channel details from elasticsearch (line 504): {entity.id}')
                entity_document = await elastic_handler.get_document_by_id(index_name=settings.TELEGRAM_CHANNELS_TOPIC_NAME, document_id=entity.id)
                if not entity_document or 'FETCH_TIME' not in entity_document or entity_document['FETCH_TIME'] < time.time() - (15*24*60*60): # 15 days
                    full_channel = await self.fetch_full_channel(entity=entity)
                    draft = ChannelExtractor.extract(obj=full_channel)
                    draft['FOLLOWERS'] = [{'FOLLOWERS': draft['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
                    if entity_document:
                        if 'FOLLOWERS' in entity_document and isinstance(entity_document['FOLLOWERS'], list):
                            draft['FOLLOWERS'].extend(entity_document['FOLLOWERS'])
                        await elastic_handler.update_document(index_name=settings.TELEGRAM_CHANNELS_TOPIC_NAME, document_id=entity.id, update_data=draft)
                    else:
                        await elastic_handler.index_document(index_name=settings.TELEGRAM_CHANNELS_TOPIC_NAME, document_id=entity.id, document=draft)
                    linked_group_username = PeerChannelExtractor.get_linked_chat_username(obj=full_channel)
                    linked_group_id = PeerChannelExtractor.get_linked_chat_id(obj=full_channel)
                else:
                    linked_group_username = entity_document.get('LINKED_GROUP_USERNAME', None)
                    linked_group_id = entity_document.get('LINKED_GROUP_ID', None)
            else:
                linked_group_username = PeerChannelExtractor.get_linked_chat_username(obj=full_channel)
                linked_group_id = PeerChannelExtractor.get_linked_chat_id(obj=full_channel)

            self.channel_id_to_top_message[entity.id] = last_message_id
            if entity.id not in self.channel_id_to_entity:
                self.channel_id_to_entity[entity.id] = entity
            if entity.id not in self.channel_ids:
                self.channel_ids.append(entity.id)

            if linked_group_id and entity.id not in self.channel_id_to_linked_group:
                self.channel_id_to_linked_group[entity.id] = {
                    'username': linked_group_username,
                    'id': linked_group_id,
                }
            await self.sync_entity_to_database(entity=entity, linked_peer_id=linked_group_id, telegram_peer=peer, _type=True, on_startup=on_startup)

        if isinstance(entity, Channel) and (entity.megagroup or entity.gigagroup):
            if not full_channel:
                logger.info(f'Fetching group details from elasticsearch (line 541): {entity.id}')
                group_document = await elastic_handler.get_document_by_id(index_name=settings.TEGRAM_GROUPS_TOPIC_NAME, document_id=entity.id)
                if not group_document or 'FETCH_TIME' not in group_document or group_document['FETCH_TIME'] < time.time() - (15*24*60*60): # 15 days
                    full_channel = await self.fetch_full_channel(entity=entity)
                    draft = GroupExtractor.extract(obj=full_channel)
                    draft['FOLLOWERS'] = [{'FOLLOWERS': draft['FOLLOWERS'], 'FETCH_TIME': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}]
                    if group_document:
                        if 'FOLLOWERS' in group_document and isinstance(group_document['FOLLOWERS'], list):
                            draft['FOLLOWERS'].extend(group_document['FOLLOWERS'])
                        await elastic_handler.update_document(index_name=settings.TEGRAM_GROUPS_TOPIC_NAME, document_id=entity.id, update_data=draft)
                    else:
                        await elastic_handler.index_document(index_name=settings.TEGRAM_GROUPS_TOPIC_NAME, document_id=entity.id, document=draft)
                    linked_channel_username = PeerChannelExtractor.get_linked_chat_username(obj=full_channel)
                    linked_channel_id = PeerChannelExtractor.get_linked_chat_id(obj=full_channel)
                else:
                    linked_channel_username = group_document.get('LINKED_CHANNEL_USERNAME', None)
                    linked_channel_id = group_document.get('LINKED_CHANNEL_ID', None)
            else:
                linked_channel_username = PeerChannelExtractor.get_linked_chat_username(obj=full_channel)
                linked_channel_id = PeerChannelExtractor.get_linked_chat_id(obj=full_channel)

            self.group_id_to_top_message[entity.id] = last_message_id
            if entity.id not in self.group_id_to_entity:
                self.group_id_to_entity[entity.id] = entity
            if entity.id not in self.group_ids:
                self.group_ids.append(entity.id)

            if linked_channel_id and entity.id not in self.group_id_to_linked_channel:
                self.group_id_to_linked_channel[entity.id] = {
                    'username': linked_channel_username,
                    'id': linked_channel_id,
                }
                self.forwarded_messages_to_discussion[entity.id] = redis_handler.lrange(key=entity.id)
                if len(self.forwarded_messages_to_discussion[entity.id]) > 100:
                    redis_handler.lpop(key=entity.id, count=len(self.forwarded_messages_to_discussion[entity.id]) - 100)
            await self.sync_entity_to_database(entity=entity, linked_peer_id=linked_channel_id, telegram_peer=peer, _type=False, on_startup=on_startup)

    async def sync_entity_to_database(self, entity, linked_peer_id=None, _type=True, on_startup=False, telegram_peer=None):
        username = ChannelExtractor.get_username(entity)

        if not telegram_peer:
            telegram_peer = peer_service.get_peer_by_peer_id(peer_id=entity.id)

        if not telegram_peer and username:
            telegram_peer = peer_service.get_peer_by_username(username=username)

        # Another account is subscribed to the channel, so leave from the channel
        if (on_startup 
            and telegram_peer 
            and telegram_peer.subscriber 
            and telegram_peer.subscriber != 1 
            and telegram_peer.subscriber != 2 
            and int(telegram_peer.subscriber) != int(self.account_phone)):
            logger.info(f' Left from channel {entity.id} because it is subscribed by another account: {telegram_peer.subscriber}')
            await self.left_from_channel(entity.id)
            return False

        # Update peer details in sql if on_startup was set or peer details is not equal to the entity
        if telegram_peer and (
            (on_startup and telegram_peer.on_waiting)
            or not telegram_peer.peer_id
            or not telegram_peer.subscriber
            or telegram_peer.subscriber == 1
            or telegram_peer.subscriber == 2
            or telegram_peer.username != username
            or telegram_peer.linked_peer_id != linked_peer_id
            or telegram_peer.is_channel != _type
        ):
            logger.info(f' Update peer details in database: {telegram_peer.id}')
            data = {
                'peer_id': entity.id,
                'username': username,
                'url': f'https://t.me/{username}' if username else None,
                'is_channel': _type,
                'blocked': False,
            }
            if linked_peer_id:
                data['linked_peer_id']= linked_peer_id
            if on_startup:
                data['subscriber'] = int(self.account_phone)
                data['on_waiting'] = False
            peer_service.update_peer(peer_id=telegram_peer.id, peer_data=data)

        # Account subscribed the peer and need to save peer details in sql
        if not telegram_peer:
            logger.info(f' Add peer details to database: {entity.id}')
            data = {
                'peer_id': entity.id,
                'username': username,
                'url': f'https://t.me/{username}' if username else None,
                'is_channel': _type,
                'blocked': False,
            }
            if linked_peer_id:
                data['linked_peer_id']= linked_peer_id
            if on_startup:
                data['subscriber'] = int(self.account_phone)
                data['on_waiting'] = False
            peer_service.create_peer(data)

        # Discussion chat not exist in sql, so create it
        if _type and linked_peer_id and not peer_service.get_peer_by_peer_id(peer_id=linked_peer_id):
            data = {'username': None, 'url': None, 'peer_id': linked_peer_id, 'linked_peer_id': entity.id, 'subscriber': 1, 'is_channel': False}
            peer_service.create_peer(data)

    async def _rebuild_entity_mappings_from_dialogs(self, dialogs=[], on_startup: bool = False):

        for dialog in dialogs:
            entity = dialog.entity
            if not getattr(entity, 'id', None):
                continue

            await self.ensure_entity_mapping(
                entity=entity,
                last_message_id=dialog.message.id,
                unread_count=dialog.unread_count,
                full_channel=None,
                on_startup=on_startup,
            )
        joinet_entities_in_db = peer_service.get_all_subscribed_peers(subscriber=int(self.account_phone))
        logger.info(f' Joinet entities in database: {joinet_entities_in_db}')
        for peer in joinet_entities_in_db:
            if peer.peer_id and peer.peer_id not in self.channel_ids and peer.peer_id not in self.group_ids:
                peer_service.unsubscribe_peer(peer_id=peer.peer_id)
    
    async def refresh_entity_mappings(self):
        dialogs = await self.client.get_dialogs()
        return await self._rebuild_entity_mappings_from_dialogs(on_startup=True, dialogs=dialogs)
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def refresh_user_mappings(self):
        self.client_entity = await self.client.get_me()
        self.user_id_to_entity[self.client_entity.id] = self.client_entity
        self.user_ids.append(self.client_entity.id)
        await self.store_entity_details(entity_id=self.client_entity.id, is_user=True)

        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            if isinstance(dialog.entity, User) and not dialog.entity.bot:
                if dialog.entity.id not in self.user_ids:
                    self.user_id_to_entity[dialog.entity.id] = dialog.entity
                    self.user_ids.append(dialog.entity.id)
                    await self.store_entity_details(entity_id=dialog.entity.id, is_user=True)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def on_test(self):
        pass

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _process_comments(self, discussion_message_id, chat_id, source_message_id, channel_username, group_username, comments_count):
        pending_media_grouped_id = None
        pending_media_messages = []

        async for comment in self.client.iter_messages(chat_id, reply_to=source_message_id, reverse=True):
            # Sleep for a random time to avoid being detected as a bot
            await asyncio.sleep(random.uniform(0.4, 1))
            if comment.reply_to_msg_id != discussion_message_id:
                continue
            try:
                # Check if the comment is a media group
                if (
                    (pending_media_grouped_id and comment.grouped_id and comment.grouped_id != pending_media_grouped_id)
                        or
                    (pending_media_grouped_id and not comment.grouped_id)
                ):
                    # Extract message details
                    if comment.reply_to_msg_id == discussion_message_id:
                        draft = ChannelCommentExtractor.extract(
                            obj=pending_media_messages[0],
                            discussion_message_id=discussion_message_id,
                            source_message_id=source_message_id,
                            source_channel_username=channel_username,
                            source_group_username=group_username,
                            source_channel_id=chat_id,
                        )

                        # Extract media details
                        for group_message in pending_media_messages[::-1][:-1]:
                            draft['MEDIA'].extend(ChannelCommentExtractor.get_media(group_message))

                        # Insert data to ksql
                        ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_MESSAGES_TOPIC_NAME)

                    # Reset media group
                    pending_media_messages = []
                    pending_media_grouped_id = None

                    # Sync new entity to database if it is a channel or group
                    if (draft['AUTHOR_ID'] and 
                        draft['AUTHOR_TYPE'] == 'CHANNEL' and 
                        (draft['AUTHOR_ID'] not in self.channel_ids) and 
                        (draft['AUTHOR_ID'] not in self.group_ids)):
                        if not peer_service.get_peer_by_peer_id(peer_id=draft['AUTHOR_ID']):
                            entity = await self.fetch_entity_by_id(draft['AUTHOR_ID'])
                            _type = False if entity.megagroup or entity.gigagroup else True
                            await self.sync_entity_to_database(entity=entity, _type=_type, on_startup=False)

                # Add comment to media group
                if comment.grouped_id:
                    pending_media_messages.append(comment)
                    pending_media_grouped_id = comment.grouped_id

                if not comment.grouped_id:
                    # Extract message details
                    if comment.reply_to_msg_id == discussion_message_id:
                        draft = ChannelCommentExtractor.extract(
                            obj=comment,
                            discussion_message_id=discussion_message_id,
                            source_message_id=source_message_id,
                            source_channel_username=channel_username,
                            source_group_username=group_username,
                            source_channel_id=chat_id,
                        )
                        # Insert data to ksql
                        ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_MESSAGES_TOPIC_NAME)

                    # Sync new entity to database if it is a channel or group
                    if (draft['AUTHOR_ID'] and 
                        draft['AUTHOR_TYPE'] == 'CHANNEL' and 
                        (draft['AUTHOR_ID'] not in self.channel_ids) and 
                        (draft['AUTHOR_ID'] not in self.group_ids)):
                        if not peer_service.get_peer_by_peer_id(peer_id=draft['AUTHOR_ID']):
                            entity = await self.fetch_entity_by_id(draft['AUTHOR_ID'])
                            _type = False if entity.megagroup or entity.gigagroup else True
                            await self.sync_entity_to_database(entity=entity, _type=_type, on_startup=False)

            except telethon.errors.AuthKeyDuplicatedError as e:
                logger.error(f'AuthKeyDuplicatedError occurred in comment processing: {e}')
            except telethon.errors.MsgIdInvalidError:
                logger.error(f'Invalid message ID: {source_message_id}')
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _process_messages(self, entity, messages, username=None, process_comment=False, route_message=False, chat=False):
        message = messages[0] if isinstance(messages, list) else messages
        entity_id = MessageExtractor.get_peer_id(message.peer_id)
        
        if chat:
            logger.info(f'Message: {message}')
            file_path = None
            if message.media:
                file_path = f'{entity_id}-{message.id}'
                file_path = await self.download_media(message.media, file_path=f'{file_path}')
            draft = ChatMessageExtractor.extract(obj=message, media_path=file_path, admin_id=self.client_entity.id)
            logger.info(f'Draft: {draft}')
            ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_CHATS_TOPIC_NAME)
            redis_handler.set(key=f'{entity_id}-chat-message', value=message.id)
            if self.client_entity.id not in self.user_ids:
                await self.store_entity_details(entity_id=self.client_entity.id, is_user=True)
            return

        if (
            entity_id in self.group_ids
            and entity_id in self.group_id_to_linked_channel
            and message.fwd_from
            and GroupMessageExtractor.get_fwd_peer_id(obj=message) == self.group_id_to_linked_channel[entity_id]['id']
        ):
            new_forwarding_details = {'message_id': message.id, 'channel_message_id': message.fwd_from.channel_post}
            self.forwarded_messages_to_discussion[entity_id].append(new_forwarding_details)
            redis_handler.rpush(entity_id, new_forwarding_details)
            if len(self.forwarded_messages_to_discussion[entity_id]) > 100:
                self.forwarded_messages_to_discussion[entity_id] = self.forwarded_messages_to_discussion[entity_id][1:]
            if len(redis_handler.lrange(entity_id)) > 100:
                redis_handler.lpop(entity_id, count=1)
            draft = GroupMessageExtractor.extract(
                obj=message,
                peer_username=username,
            )
            if isinstance(messages, list):
                for group_message in messages[::-1][:-1]:
                    if draft['MEDIA']:
                        draft['MEDIA'].extend(MessageExtractor.get_media(group_message))
                    else:
                        draft['MEDIA'] = MessageExtractor.get_media(group_message)
            ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_MESSAGES_TOPIC_NAME)
        elif (
            entity_id in self.group_ids
            and message.reply_to 
            and any(
                msg.get('message_id', 0) == message.reply_to.reply_to_msg_id
                for msg in self.forwarded_messages_to_discussion[entity_id]
            )
        ):
            forwarding_details = self.forwarded_messages_to_discussion[entity_id]
            for msg in forwarding_details:
                if msg.get('message_id', 0) == message.reply_to.reply_to_msg_id:
                    source_message_id = msg.get('channel_message_id', 0)
                    break
            draft = ChannelCommentExtractor.extract(
                obj=message, 
                discussion_message_id=message.id,
                source_message_id=source_message_id,
                source_channel_username=self.group_id_to_linked_channel[entity_id]['username'],
                source_group_username=username,
                source_channel_id=self.group_id_to_linked_channel[entity_id]['id'],
            )
            if isinstance(messages, list):
                for group_message in messages[::-1][:-1]:
                    if draft['MEDIA']:
                        draft['MEDIA'].extend(MessageExtractor.get_media(group_message))
                    else:
                        draft['MEDIA'] = MessageExtractor.get_media(group_message)
            ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_MESSAGES_TOPIC_NAME)        
        else:
            draft = (ChannelMessageExtractor if entity_id in self.channel_ids else GroupMessageExtractor).extract(
                obj=message, 
                peer_username=username,
            )
            if isinstance(messages, list):
                for group_message in messages[::-1][:-1]:
                    if draft['MEDIA']:
                        draft['MEDIA'].extend(MessageExtractor.get_media(group_message))
                    else:
                        draft['MEDIA'] = MessageExtractor.get_media(group_message)
            ksql_handler.insert_data(data=draft, stream_name=settings.TELEGRAM_MESSAGES_TOPIC_NAME)

            if route_message and entity_id in self.channel_ids:
                await message_router_service.route_message(message, entity, username, self.channel_ids)

            if (process_comment
                and message.replies
                and message.replies.replies > 0
                and datetime.isoformat(draft['DATE']) < datetime.now() - timedelta(hours=6)
                and entity_id in self.channel_ids 
                and entity_id in self.channel_id_to_linked_group
                and message.id not in [msg['channel_message_id'] for msg in redis_handler.lrange(key=self.channel_id_to_linked_group[entity_id]['id'])]):
                discuttion_message_details = await self.get_discuttion_details(entity=entity_id, message_id=message.id)
                if discuttion_message_details:
                    discussion_message_id = discuttion_message_details.messages[0].id
                    await self._process_comments(
                        discussion_message_id=discussion_message_id,
                        chat_id=entity_id,
                        source_message_id=message.id,
                        channel_username=username,
                        group_username=self.channel_id_to_linked_group[entity_id]['username'],
                        comments_count=draft['REPLIES_COUNT'],
                    )
                else:
                    logger.warning(f"Comment for this message is not allowed by the admin: {message.id}")

        if draft['FWD_PEER_ID'] and draft['FWD_PEER_ID'] not in self.channel_ids and draft['REPLY_PEER_ID'] not in self.group_ids:
            await self.store_entity_details(entity_id=draft['FWD_PEER_ID'])
        if draft['REPLY_PEER_ID'] and draft['REPLY_PEER_ID'] not in self.channel_ids and draft['REPLY_PEER_ID'] not in self.group_ids:
            await self.store_entity_details(entity_id=draft['REPLY_PEER_ID'])
        if draft['AUTHOR_TYPE'] == 'USER':
            await self.store_entity_details(entity_id=draft['AUTHOR_ID'], is_user=True)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def _process_message_batch(
        self,
        entity_id, # channel or group id
        start_message_id, # message id
        end_message_id, # message id
        username, # channel or group username
        entity=None, # channel or group entity
        message_ids=None, # message ids
        BATCH_SIZE_TO_READ=100,
        process_comments=False,
        route_message=False,
        chat=False
    ):
        if start_message_id and start_message_id > 1:
            start_message_id -= 1
        if end_message_id:
            end_message_id += 1

        pending_media_grouped_id = None
        pending_media_messages = []
        first_batch = True

        # If update request is triggered for some messages of specific channel.
        if message_ids:
            messages = await self.client.get_messages(entity_id, ids=message_ids)
            for message in messages:
                if message:
                    await self._process_messages(entity=entity, messages=message, username=username, process_comment=False, route_message=False, chat=False)
            return

        # If update or process_new_chat_messages called for a telegram chat
        if chat:
            while True:
                try:
                    messages = await self.client.get_messages(entity_id, limit=end_message_id)
                    break
                except telethon.errors.FloodWaitError as e:
                    logger.warning(f"Flood wait: sleeping for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                    continue

            for message in messages:
                if not message or not message.message:
                    continue
                if (
                    (pending_media_grouped_id and message.grouped_id and message.grouped_id != pending_media_grouped_id)
                        or
                    (pending_media_grouped_id and not message.grouped_id)
                ):
                    await self._process_messages(entity=entity, messages=pending_media_messages, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
                    pending_media_messages = []
                    pending_media_grouped_id = None

                if message.grouped_id:
                    pending_media_messages.append(message)
                    pending_media_grouped_id = message.grouped_id

                if not message.grouped_id:
                    await self._process_messages(entity=entity, messages=message, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
            await self.client.send_read_acknowledge(entity, messages[0])
            return
        
        # If update request called for a telegram channel or group
        while True:
            try:
                messages = await self.client.get_messages(entity_id, offset_id=start_message_id, limit=min(BATCH_SIZE_TO_READ, end_message_id - start_message_id), reverse=True)
            except telethon.errors.FloodWaitError as e:
                logger.warning(f"Flood wait: sleeping for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
                continue

            messages = sorted(messages, key=lambda x: x.id)

            if not messages:
                if pending_media_grouped_id:
                    await self._process_messages(entity=entity, messages = pending_media_messages, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
                return

            # Update offset for next batch of messages
            start_message_id = messages[-1].id

            if first_batch and messages[0].grouped_id and not messages[0].message:
                first_batch = False
                message_grouped_id = messages[0].grouped_id
                start_index = 1
                while start_index < len(messages) and messages[start_index].grouped_id == message_grouped_id:
                    start_index += 1
                messages = messages[start_index:]

            for message in messages:
                first_batch = False
                # Check termination condition if reatched to last message id or raised out of missed update range. 
                if end_message_id and message.id >= end_message_id:
                    if pending_media_grouped_id:
                        await self._process_messages(entity=entity, messages=pending_media_messages, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
                    return
                if not end_message_id and datetime.isoformat(ChannelMessageExtractor.get_date(obj=message)) > datetime.now() - timedelta(hours=6):
                    if pending_media_grouped_id:
                        await self._process_messages(entity=entity, messages=pending_media_messages, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
                    return
                if (
                    (pending_media_grouped_id and message.grouped_id and message.grouped_id != pending_media_grouped_id)
                        or
                    (pending_media_grouped_id and not message.grouped_id)
                ):
                    await self._process_messages(entity=entity, messages=pending_media_messages, username=username, process_comment=process_comments, route_message=route_message, chat=chat)
                    pending_media_messages = []
                    pending_media_grouped_id = None

                if message.grouped_id:
                    pending_media_messages.append(message)
                    pending_media_grouped_id = message.grouped_id

                if not message.grouped_id:
                    await self._process_messages(entity=entity, messages=message, username=username, process_comment=process_comments, route_message=route_message, chat=chat)

            await asyncio.sleep(3)
            logger.info(f'Collected {len(messages)} messages from {entity_id}')

    async def on_get_new_chat_messages_range(self):
        if 'admin_listener' in self.account_roles:
            for peer_id in self.user_ids:
                self.new_chat_messages_to_fetch[peer_id] = await entity_range_service.get_chat_last_message_id(user_id=peer_id)

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def process_new_chat_messages(self, entity_id, entity, BATCH_SIZE_TO_READ=100):
        end_message_id = await self.get_last_message_id(chat_id=entity_id)
        start_message_id = self.new_chat_messages_to_fetch[entity_id]
        
        if start_message_id and end_message_id and start_message_id < end_message_id:
            logger.info(f'NEW MESSAGES OF: {entity_id} from: {start_message_id} to {end_message_id}')
            username = UserExtractor.get_username(entity)

            await self._process_message_batch(
                entity_id=entity_id,
                start_message_id=start_message_id,
                end_message_id=end_message_id,
                username=username,
                entity=entity,
                BATCH_SIZE_TO_READ=BATCH_SIZE_TO_READ,
                process_comments=False,
                route_message=False,
                chat=True,
            )
        else:
            logger.info(f'No messages found for {entity_id}, start_message_id: {start_message_id}, end_message_id: {end_message_id}')

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def update_messages(self, chat_id, entity, message_ids: List[int]=None, BATCH_SIZE_TO_READ=100):
        channel_username = PeerChannelExtractor.get_username(entity)

        if message_ids:
            logger.info(f"Updating messages {message_ids} of peer_id: {chat_id}.")

            await self._process_message_batch(
                entity_id=chat_id,
                start_message_id=None,
                end_message_id=None,
                message_ids=message_ids,
                username=channel_username,
                entity=entity,
                BATCH_SIZE_TO_READ=BATCH_SIZE_TO_READ,
                process_comments=False,
                route_message=False,
                chat=False
            )
            await self.store_entity_details(entity_id=chat_id, is_user=True)
        
        else:
            await self.store_entity_details(entity_id=chat_id, is_user=False)
            start_message_id = await entity_range_service.get_update_range(peer_id=chat_id)
            if not start_message_id:
                logger.info(f"No unupdated range found for {chat_id}, start_message_id: {start_message_id} to last message")
                return
            logger.info(f"Updating messages of {chat_id} from {start_message_id} to last message.")

            await self._process_message_batch(
                entity_id=chat_id,
                start_message_id=start_message_id,
                end_message_id=None,
                username=channel_username,
                entity=entity,
                BATCH_SIZE_TO_READ=BATCH_SIZE_TO_READ,
                process_comments=True,
                route_message=False,
                chat=False
            )

    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def handle_new_message(self, event):

        entity_id = MessageExtractor.get_peer_id(event.message.peer_id)

        if ('collector' in self.account_roles) and (event.text) and ((entity_id in self.channel_ids) or (entity_id in self.group_ids)):
            redis_handler.set(key=f'{entity_id}-top', value=event.message.id)

            entity = self.channel_id_to_entity.get(entity_id) or self.group_id_to_entity.get(entity_id)
            username = PeerChannelExtractor.get_username(obj=entity)
            logger.info(f'NEW MESSAGE https://t.me/{"c/" + str(entity_id) if not username else username}/{event.message.id}')

            await self._process_messages(entity=entity, messages=event.message, username=username, process_comment=False, route_message=True, chat=False)
            await self.client.send_read_acknowledge(entity_id, event.message)
            return

        if isinstance(event.message.peer_id, PeerUser) and 'admin_listener' in self.account_roles:
            logger.info(f'EVENT MESSAGE: {event}')
            await self.client.send_read_acknowledge(entity_id, event.message)
            await self._process_messages(entity=None, messages=event.message, username=None, process_comment=False, route_message=False, chat=True)
    
    @retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
    async def handle_send_message(self, user_id, reply_to_msg_id, message, media_files=[]):
        media_list = []
        temp_files = []
        
        try:
            for media_file in media_files:
                # Decode base64 data
                file_data = base64.b64decode(media_file['data'])
                
                # Create temporary file
                file_extension = os.path.splitext(media_file['filename'])[1] or '.bin'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
                temp_files.append(temp_file.name)
                
                # Write binary data to temp file
                temp_file.write(file_data)
                temp_file.close()
                
                media_list.append(temp_file.name)
            
            if media_list:
                result = await self.client.send_message(
                    entity=user_id,
                    message=message,
                    reply_to=reply_to_msg_id,
                    file=media_list
                )
            else:
                result = await self.client.send_message(
                    entity=user_id,
                    message=message,
                    reply_to=reply_to_msg_id
                )
            logger.info(result)
            if result:
                await self._process_messages(entity=None, messages=result, username=None, process_comment=False, route_message=False, chat=True)
            return result
        
        finally:
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to delete temp file {temp_file_path}: {e}")
