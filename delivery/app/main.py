import fastapi
from fastapi import HTTPException
from contextlib import asynccontextmanager
import asyncio
import threading

# App imports
from utils.kafka_dispatcher import KafkaDispatcher
from app.startup import proxy_server, redis_db
from app.config import *
from app.schemas import *
from app.telegram.api import TelegramBotWorker

print(KAFKA_BOOTSTRAP_SERVERS, flush=True)

telegram_worker = None
telegram_worker = None
consumer = None

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Periodically reload channel subscription
async def updated_subscription():
    while True:
        await asyncio.sleep(5 * 60)
        try:
            logger.info("Updating bot targets...")
            consumer.refresh_consumer()
        except Exception as e:
            logger.error(f"Error updating bots: {e}")


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    global bot_manager, telegram_worker, consumer
    try:
        # Message delivery for telegram
        telegram_worker = TelegramBotWorker(redis_client=redis_db)
        consumer = KafkaDispatcher(
            kafka_host=KAFKA_BOOTSTRAP_SERVERS,
            worker=telegram_worker,
            config_path='/utils/',
            group_id='TELEGRAM_KAFKA_GROUP_ID',
        )

        asyncio.create_task(consumer.run())
        logger.info("Background tasks started successfully.")
    except Exception as e:
        logger.error(f"Startup failure: {e}")
        raise

    yield

    logger.info("Shutting down...")


app = fastapi.FastAPI(lifespan=lifespan, root_path="/delivery")

@app.post('/health')
async def send_file(payload: FilePayload):
    return fastapi.responses.JSONResponse(content={"status": "ok"}, status_code=200)


@app.post('/send_file')
async def send_file(payload: FilePayload):
    try:
        return await telegram_worker.send_file(
            channel_id=-payload.channel_id,
            file_path=payload.file_path,
            caption=payload.caption,
            pin=payload.pin,
        )
    except FileNotFoundError:
        logger.error(f"File not found: {payload.file_path}")
        return {"status": "file not found"}
    except Exception as e:
        logger.error(f"Unexpected error while sending file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# @app.post('/pin_message')
# async def send_file(payload: FilePayload):
#     try:
#         response = await telegram_worker.process_file(
#             channel_id=-payload.channel_id,
#             file_path=payload.file_path,
#             tags=payload.tags
#         )
#         if response:
#             telegram_worker.pin_message(
#                 channel_id=payload.channel_id,
#                 message_id=response['message_id'],
#             )
#     except Exception as e:
#         logger.error(f"Unexpected error while sending message: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
