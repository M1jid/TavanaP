import os
from datetime import datetime

import telethon

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.telegram_client import TelegramClient
from app.telegram import exceptions as exceptions
from app.services import telegram_peer as peer_service
from app.services import telegram_account as account_service
from app.core.config import settings
from app.services.monitoring.monitoring import get_monitor, AccountStatus
from app.services import entity_range_service
from app.startup import kafka_producer, elastic_handler
from app.schemas.telegram_account import TelegramSchemaResponseAccount


class AccountManager:
    def __init__(self, account: TelegramSchemaResponseAccount):
        self.account = account
        
        # Initialize monitoring
        self.monitor = get_monitor(self.account.id, self.account.phone, elastic_handler)
        
        logger.info(
            (
                f"api_id: {account.api_id}\n"
                f"api_hash: {account.api_hash}\n"
                f"phone: {self.account.phone}\n"
                f"session_name: {account.session_file}\n"
            )
        )
        
        self.telegram_client = TelegramClient(account=account)

    async def on_start(self):
        await self.on_connect()
        await self.on_refresh_entity_mappings()

    async def on_connect(self):
        try:
            await self.telegram_client.start_client()
        except telethon.errors.AuthKeyDuplicatedError as e:
            logger.error(f'An error occurred connection process: {e}')
            await self.on_disconnect()
            await self.monitor.log_connection_status(AccountStatus.ERROR, "Error occurred connection process")
            return
        except Exception as e:
            logger.error(f'An error occurred connection process: {e}')
            await self.monitor.log_connection_status(AccountStatus.ERROR, "Error occurred connection process")
            return

    async def on_refresh_entity_mappings(self):
        if 'collector' in self.account.roles: # Refresh channel entity mappings
            await self.telegram_client.refresh_entity_mappings()
        if 'admin_listener' in self.account.roles: # Refresh user entity mappings
            await self.telegram_client.refresh_user_mappings()

    async def on_event_handler(self):
        await self.telegram_client.register_the_event_handler()

    async def on_test(self):
        await self.telegram_client.on_test()

    async def on_get_new_chat_messages_range(self):
        await self.telegram_client.on_get_new_chat_messages_range()

    async def on_new_messages(self):
        if 'admin_listener' in self.account.roles:
            for user_id, missed_range in self.telegram_client.new_chat_messages_to_fetch.items():
                if missed_range[1] == 0:
                    continue
                entity = self.telegram_client.user_id_to_entity[user_id]
                await self.telegram_client.process_new_chat_messages(user_id, entity, BATCH_SIZE_TO_READ=100)

    async def on_update_messages(self):
        if 'collector' in self.account.roles:
            for channel_id, entity in self.telegram_client.channel_id_to_entity.items():
                await self.telegram_client.update_messages(chat_id=channel_id, entity=entity)
            for channel_id, entity in self.telegram_client.group_id_to_entity.items():
                await self.telegram_client.update_messages(chat_id=channel_id, entity=entity)

    async def on_update_specific_messages(self, peer_id, message_ids, job_id=None):
        if 'collector' in self.account.roles and (peer_id in self.telegram_client.group_ids or peer_id in self.telegram_client.channel_ids):
            try:
                entity = self.telegram_client.channel_id_to_entity[peer_id] if peer_id in self.telegram_client.channel_id_to_entity else self.telegram_client.group_id_to_entity[peer_id]
                await self.telegram_client.update_messages(chat_id=peer_id, entity=entity, message_ids=message_ids)
                await self.on_update_specific_messages_acknowledgment(job_id, peer_id, "completed", f"successfully updated {len(message_ids)} messages for peer {peer_id}")
                await self.monitor.log_acknowledgment(job_id, str(peer_id), "completed", f"successfully updated {len(message_ids)} messages for peer {peer_id}")
            except KeyError as e:
                logger.error(f"Entity not found for peer {peer_id}")
                if job_id:  
                    await self.on_update_specific_messages_acknowledgment(job_id, peer_id, "failed", f"Entity not found for peer {peer_id}")
    
    async def on_update_specific_messages_acknowledgment(self, job_id: str, peer_id: int, status: str, error_message: str = None):
        """Send acknowledgment back to report service via Kafka"""
        await kafka_producer.produce(
            topic=settings.TELEGRAM_UPDATE_ACK_TOPIC,
            value={
                "job_id": job_id,
                "peer_id": peer_id,
                "status": status,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            },
            key=str(peer_id)
        )        
        logger.info(f"Sent acknowledgment for job {job_id}, peer {peer_id}: {status}")

    async def on_send_message(self, user_id, reply_to_msg_id, message, media_files=[]):
        return await self.telegram_client.handle_send_message(user_id, reply_to_msg_id, message, media_files)

    async def on_disconnect(self):
        if os.getenv("MODE") == "PRODUCTION":
            account_service.drop_account(self.account.id)
        logger.info("Disconnecting from Telegram client.")
        await self.telegram_client.client.disconnect()

    async def on_join_new_channels(self, MAX_JOINING_CHANNELS=5):
        if 'collector' in self.account.roles:
            new_entity_counts = 0
            while new_entity_counts < MAX_JOINING_CHANNELS:
                logger.info(f"Joining new entity {new_entity_counts + 1}/{MAX_JOINING_CHANNELS}...")

                try:
                    peer = peer_service.acquire_telegram_peer(subscriber=self.account.phone)
                    if not peer:
                        logger.info(f"No available peers left.")
                        break
                    logger.info(f"New entity to subscribe by {self.account.phone}: {peer}")
                    await self.telegram_client.join_new_entity(peer=peer)
                    new_entity_counts+=1
                except telethon.errors.FloodWaitError:
                    logger.error(f'More than 100 seconds flood wait raised. Skip joining new channels.')
                    peer_service.unsubscribe_peer(peer_id=peer.peer_id)
                    break
                except telethon.errors.ChannelInvalidError as e:
                    logger.error(f"Invalid telegram channel. not found. {e}")
                    peer_service.unsubscribe_peer(peer_id=peer.peer_id)
                    peer_service.block_peer(peer_id=peer.peer_id)
                    continue
                except exceptions.CustomChannelsTooMuchError as e:
                    logger.error(f"Joining request error: {e}")
                    peer_service.unsubscribe_peer(peer_id=peer.peer_id)
                    break
                except telethon.errors.ChannelsTooMuchError as e:
                    logger.error(f"Joining request error. {e}")
                    peer_service.unsubscribe_peer(peer_id=peer.peer_id)
                    break
                except exceptions.UsernameNotFound as e:
                    logger.error(f"Username {peer['url']} not found")
                    peer_service.unsubscribe_peer(peer_id=peer.peer_id)
                    peer_service.block_peer(peer_id=peer.peer_id)
                    continue
                except Exception as e:
                    if hasattr(e, 'status_code') and e.status_code == 404:
                        logger.info('There is no more channel')
                        return
                    else:
                        # Log general exception
                        await self.monitor.log_channel_update(
                            channel_id=str(peer.peer_id),
                            channel_username=peer.url,
                            status=AccountStatus.ERROR,
                            message=f"General exception: {str(e)}"
                        )
