"""
Application startup module for the Telegram application.

This module handles the application lifecycle management.
"""

import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Set up scheduler and timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from pytz import timezone

from app.core.config import settings
from app.startup.infrastructure import setup_all_infrastructure

# Telegram client
from app.telegram.account_manager import AccountManager
from app.telegram.client_registry import ClientRegistry
from app.services.monitoring.monitoring_dashboard import router as monitoring_router
from app.services import telegram_account as account_service
from app.schemas.telegram_account import TelegramSchemaResponseAccount
from app.startup.infrastructure import (
    # kafka_delete_middle_connectors,
    kafka_create_middle_connectors,
    kafka_wait_for_middle_topics,
    kafka_create_middle_streams
)

# Kafka event handler
from utils.kafka_handler import KafkaHandler, KafkaMessage

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
iran_tz = timezone("Asia/Tehran")

# Global Kafka handler for background listening
kafka_handler = None


async def handle_new_message(message: KafkaMessage):
    """Handle new message events from Kafka."""
    value = message.value
    admin_client = await ClientRegistry.get_client_by_id(value['admin_phone'])
    import traceback

    if not admin_client:
        return
    try:
        return await admin_client.on_send_message(
            user_id=value['user_id'],
            reply_to_msg_id=value['reply_to_msg_id'],
            message=value['text'],
            media_files=value['media_files']
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        logger.error(' '.join(traceback.format_exception(type(e), e, e.__traceback__)))


async def handle_update_messages(message: KafkaMessage):
    """Handle message update events from Kafka."""
    peer = int(message.key)
    message_data = message.value
    
    # Handle both old format (just message_ids) and new format (with job_id)
    if isinstance(message_data, list):
        # Old format: just message_ids
        message_ids = message_data
        job_id = None
    else:
        # New format: dict with message_ids, job_id, peer_id
        message_ids = message_data.get("message_ids", [])
        job_id = message_data.get("job_id")
    
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_update_specific_messages(peer, message_ids, job_id) for client in clients))


async def setup_kafka_listener():
    """Set up Kafka listener in the main event loop."""
    global kafka_handler
    
    kafka_handler = KafkaHandler()
    
    # Register callback functions
    kafka_handler.add_listener(settings.TELEGRAM_CHATS_MESSAGE_SEND_TOPIC, handle_new_message)
    kafka_handler.add_listener(settings.TELEGRAM_UPDATE_MESSAGE, handle_update_messages)
    
    # Start listening
    await kafka_handler.start_listener(
        topics=[settings.TELEGRAM_CHATS_MESSAGE_SEND_TOPIC, settings.TELEGRAM_UPDATE_MESSAGE],
        group_id=os.getenv("HOSTNAME", None)
    )
    
    logger.info("Kafka listener started in main event loop")
    return kafka_handler


async def stop_kafka_listener():
    """Stop Kafka listener gracefully."""
    global kafka_handler
    
    if kafka_handler:
        try:
            await kafka_handler.stop_listener()
            await kafka_handler.close()
            logger.info("Kafka listener stopped gracefully")
        except Exception as e:
            logger.error(f"Error stopping Kafka listener: {e}")
        finally:
            kafka_handler = None


async def run_test_for_all_clients():
    """Run test for all clients."""
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_test() for client in clients))


async def trigger_event_handler_for_all_clients():
    """Trigger event handler for all clients."""
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_event_handler() for client in clients))


################# Scheduler functions ################
async def schedule_update_messages_for_account(account: TelegramSchemaResponseAccount):
    """Schedule function to update messages for a specific account."""
    start_time = datetime.now()
    logger.info(f"Starting update messages for account {account.phone}")
    
    # Get the specific client
    client = await ClientRegistry.get_client_by_id(account.id)
    if not client:
        logger.error(f"Client with phone {account.phone} not found")
        return
    
    try:
        await client.on_update_messages()
        end_time = datetime.now()
        duration = (end_time - start_time)
        logger.info(f"Account {account.phone} update completed at {end_time.strftime('%H:%M:%S')} (took {duration.total_seconds():.1f}s)")
        
        # Schedule the next job for this specific account
        await schedule_next_update_messages_for_account(account.phone, duration)
        
    except Exception as e:
        logger.error(f"Error updating messages for account {account.phone}: {e}")
        # Even if there's an error, schedule the next run
        await schedule_next_update_messages_for_account(account.phone, timedelta(seconds=0))


async def schedule_next_update_messages_for_account(account: TelegramSchemaResponseAccount, duration):
    """Schedule the next job for a specific account based on job duration."""
    # Add a small delay to ensure the current job is completely finished
    await asyncio.sleep(0.1)
    
    # Create/update connectors for this account
    await kafka_create_middle_connectors(connectors=[account.phone])
    
    if duration.total_seconds() > 60*60*6:  # 6 hours
        next_run_time = datetime.now() + timedelta(minutes=1)
    else:
        # If job took less than 6 hours, wait the remaining time to make it 6 hours total
        remaining_time = 60*60*6 - duration.total_seconds()
        next_run_time = datetime.now() + timedelta(seconds=remaining_time)
    
    logger.info(f"Scheduling next update for account {account.phone} at {next_run_time.strftime('%H:%M:%S')}")
    
    scheduler.add_job(
        schedule_update_messages_for_account, 
        DateTrigger(run_date=next_run_time),
        args=[account],  # Pass the account phone as argument
        id=f'schedule_update_messages_{account.phone}',
        replace_existing=True
    )


async def schedule_join_new_channels():
    """Schedule function to join new channels for all clients."""
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_join_new_channels() for client in clients))


async def schedule_refresh_entity_mappings():
    """Schedule function to reload channels and sync them to database."""
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_refresh_entity_mappings() for client in clients))


################# Setup scheduler ################
async def setup_scheduler():
    """Setup and start the scheduler with periodic tasks."""
    # Get all clients and schedule individual update jobs for each account
    clients = await ClientRegistry.get_all_clients()
    
    for client in clients:
        account = client.account
        # Schedule the first update for each account to run in 1 minute
        scheduler.add_job(
            schedule_update_messages_for_account, 
            DateTrigger(run_date=datetime.now() + timedelta(minutes=1)),
            args=[account],
            id=f'schedule_update_messages_{account.phone}'
        )
        logger.info(f"Scheduled update job for account {account.phone}")

    scheduler.add_job(schedule_join_new_channels, IntervalTrigger(minutes=15), max_instances=1)
    scheduler.add_job(schedule_refresh_entity_mappings, IntervalTrigger(days=1), max_instances=1)
    scheduler.start()
    logger.info(f'Scheduler started with {len(clients)} individual account update jobs')


async def schedule_new_account_updates(account: TelegramSchemaResponseAccount):
    """Schedule update jobs for a newly added account."""
    # Schedule the first update for the new account to run in 1 minute
    scheduler.add_job(
        schedule_update_messages_for_account, 
        DateTrigger(run_date=datetime.now() + timedelta(minutes=1)),
        args=[account],
        id=f'schedule_update_messages_{account.phone}'
    )
    logger.info(f"Scheduled update job for new account {account.phone}")


async def initialize_clients_static():
    """Initialize the specified number of Telegram clients from the static list."""
    accounts = [
        {
            'api_id': 2040,
            'api_hash': 'b18441a1ff607e10a989891a5462e627',
            'phone': 573174433691,
            'id': 1,
            'session_file': '573174433691.session',
            'roles': ['collector'],
            'process': 0,
        }
    ]
    
    for account in accounts:
        # Validate and create a TelegramSchemaResponseAccount object from the account dict
        account_obj = TelegramSchemaResponseAccount.model_validate(account)
        connector = AccountManager(
            account=account_obj,
        )
        await ClientRegistry.add_client(connector)


async def initialize_clients_from_db(num_clients: int = 5):
    """Initialize the specified number of Telegram clients."""
    for _ in range(num_clients):
        with account_service.acquire_telegram_account() as account:
            if account:
                connector = AccountManager(
                    account=account,
                )
                await ClientRegistry.add_client(connector)
            else:
                logger.error("No available accounts left.")
                break


async def connect_all_clients():
    """Connect all initialized clients."""
    clients = await ClientRegistry.get_all_clients()
    logger.info(f'Attempting to connect to {len(clients)} accounts...')
    await asyncio.gather(*(client.on_start() for client in clients))


async def disconnect_all_clients():
    """Gracefully disconnect all clients."""
    clients = await ClientRegistry.get_all_clients()
    await asyncio.gather(*(client.on_disconnect() for client in clients))


async def start_kafka_listener():
    """Start Kafka listener in the main event loop."""
    try:
        logger.info("Starting Kafka listener in main event loop...")
        await setup_kafka_listener()
        logger.info("Kafka listener started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Kafka listener: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown logic."""
    # Startup logic
    try:
        # Setup infrastructure
        if not await setup_all_infrastructure():
            raise Exception("Infrastructure setup failed")
        
        # Initialize clients
        if os.getenv("MODE") == "DEVELOPMENT":
            await initialize_clients_static()
        if os.getenv("MODE") == "PRODUCTION":
            await initialize_clients_from_db(num_clients=5)

        # Connect all clients
        await connect_all_clients()

        # Run test for all clients
        await run_test_for_all_clients()
        
        # Create middle connectors
        # clients = await ClientRegistry.get_all_clients()
        # await kafka_create_middle_connectors(connectors=[client.account.phone for client in clients])
        # await kafka_wait_for_middle_topics(topics=[client.account.phone for client in clients])
        # await kafka_create_middle_streams(streams=[client.account.phone for client in clients])

        # Trigger register event handler for all clients
        await trigger_event_handler_for_all_clients()
        # await kafka_delete_middle_connectors(connectors=[client.account.phone for client in clients])
        
        # Setup scheduler
        await setup_scheduler()
        
        # Start Kafka listener in main event loop
        await start_kafka_listener()

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield  # Yield to allow app startup
    
    # Shutdown logic
    logger.info("Application shutting down")
    await stop_kafka_listener()
    await disconnect_all_clients()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        lifespan=lifespan,
        title="Telegram Data Collector",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        root_path="/telegram",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include monitoring dashboard
    app.include_router(monitoring_router)

    @app.get("/accounts")
    async def get_accounts():
        return await ClientRegistry.get_all_clients()
    
    # Telegram-specific endpoints
    @app.post("/connect", summary="Connect into new account")
    async def new_account():
        try:
            account = account_service.acquire_telegram_account()
            client = AccountManager(
                account=account,
            )
            await client.on_start()
            await ClientRegistry.add_client(client)
            
            # Schedule update jobs for the new account
            await schedule_new_account_updates(account)
            
            return account
        except Exception as e:
            logger.error(f"Failed to connect new account: {e}")
            raise HTTPException(status_code=404, detail='Account was not found')
    
    return app
