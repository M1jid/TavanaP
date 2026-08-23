from functools import wraps
import traceback
import asyncio
import telethon
import time

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils.logstash_handler import logger as logstash
from app.services.monitoring.monitoring import get_monitor, AccountStatus, OperationType, LogLevel
from app.startup import elastic_handler


RETRY_REASONS = [
    "Connection to Telegram failed 5 time(s)",
    "connection to Telegram failed 5 time(s)",
    "cannot send requests while disconnected",
    "client not connected",
    "proxyconnectionerror",
    "failed to reconnect client",
    "The authorization key (session file) was used under two different IP addresses simultaneously, and can no longer be used. Use the same session exclusively, or use different sessions (caused by InvokeWithLayerRequest(InitConnectionRequest(GetConfigRequest)))"
]


def retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None):
    """
    Decorator to retry an async function on Telegram connection errors with exponential backoff.
    If client is disconnected, attempts to reconnect before retrying.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            delay = initial_delay
            start_time = time.time() if max_total_wait else None
            operation_start = time.time()
            
            instance = args[0] if args else None

            while max_attempts is None or attempt <= max_attempts:
                try:
                    logger.info(f"Attempt {attempt} to execute {func.__name__}...")
                    client = getattr(instance, "client", None)

                    # Reconnect if client is disconnected
                    if client and not client.is_connected():
                        logger.warning("Client is disconnected. Attempting to reconnect...")
                        await client.connect()
                        if not client.is_connected():
                            raise RuntimeError("Failed to reconnect client")
                    result = await func(*args, **kwargs)
                    logger.info(f"Successfully executed {func.__name__}")

                    # Enhanced monitoring
                    if func.__name__ == 'refresh_entity_mappings' \
                    or func.__name__ == 'refresh_user_mappings' \
                    or func.__name__ == 'on_test' \
                    or func.__name__ == "register_the_event_handler" \
                    or func.__name__ == "start_client":
                        if func.__name__ == 'refresh_entity_mappings':
                            operation = OperationType.REFRESH_ENTITY_MAPPINGS
                        elif func.__name__ == 'refresh_user_mappings':
                            operation = OperationType.REFRESH_USER_MAPPINGS
                        elif func.__name__ == 'on_test':
                            operation = OperationType.ON_TEST
                        elif func.__name__ == 'register_the_event_handler':
                            operation = OperationType.REGISTER_THE_EVENT_HANDLER
                        elif func.__name__ == 'start_client':
                            operation = OperationType.START_CLIENT
                        account_id = getattr(instance, 'account_account_id', 'unknown')
                        phone = getattr(instance, 'account_phone', 'unknown')
                        monitor = get_monitor(account_id, phone, elastic_handler)
                        duration_ms = int((time.time() - operation_start) * 1000)
                        await monitor.log_operation(
                            operation=operation,
                            status=AccountStatus.CONNECTED,
                            level=LogLevel.INFO,
                            message=f"Successfully executed {func.__name__}",
                            duration_ms=duration_ms,
                            metadata={"function": func.__name__, "attempt": attempt}
                        )
                    return result
                except telethon.errors.rpcerrorlist.InviteHashExpiredError:
                    raise
                except (telethon.errors.rpcerrorlist.UsernameNotOccupiedError, ValueError):
                    raise
                except telethon.errors.rpcerrorlist.UserAlreadyParticipantError:
                    raise
                except asyncio.IncompleteReadError as e:
                    await asyncio.sleep(3)
                    attempt += 1
                    continue
                except telethon.errors.FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    attempt += 1
                    continue
                except (Exception, RuntimeError)as e:
                    logger.info('-'*200)
                    logger.warning(f"failed in {func.__name__}: {e}")
                    msg = str(e)

                    # Handle specific retry conditions
                    if msg in RETRY_REASONS:
                        logstash.error({
                            'PLATFORM': 'TELEGRAM',
                            'ACCOUNT': getattr(instance, "phone", None),
                            'TYPE': 'CONNECTION_ERROR',
                            'DESC': f"Attempt {attempt} failed in {func.__name__}: {e}"
                        })
                        logger.warning(f"Attempt {attempt} failed in {func.__name__}: {e}")

                        if max_total_wait and (time.time() - start_time) > max_total_wait:
                            logger.error(f"Max total wait time ({max_total_wait}s) exceeded for {func.__name__}.")
                            raise RuntimeError(f"Failed to execute {func.__name__} after {attempt} attempts")

                        logger.warning(f"Attempt {attempt} Retry after {delay} seconds...")
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, 60)
                        attempt += 1
                    else:
                        logger.error('-'*100)
                        logger.error(' '.join(traceback.format_exception(type(e), e, e.__traceback__)))
                        return
            raise RuntimeError(f"Failed to execute {func.__name__} after {max_attempts} attempts")
        return wrapper
    return decorator
