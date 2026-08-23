"""
Enhanced monitoring and logging system for Telegram data collection
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class AccountStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    BANNED = "banned"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

class OperationType(Enum):
    REFRESH_ENTITY_MAPPINGS = "REFRESH_ENTITY_MAPPINGS"
    REFRESH_USER_MAPPINGS = "REFRESH_USER_MAPPINGS"
    UPDATE_ENTITY = "UPDATE_ENTITY"
    UPDATE_USER = "UPDATE_USER"
    UPDATE_PEER_MESSAGES = "UPDATE_PEER_MESSAGES"
    UPDATE_CHAT_MESSAGES = "UPDATE_CHAT_MESSAGES"
    FETCH_MISSING_MESSAGES = "FETCH_MISSING_MESSAGES"
    REGISTER_THE_EVENT_HANDLER = "REGISTER_THE_EVENT_HANDLER"
    START_CLIENT = "START_CLIENT"
    CONNECTION = "CONNECTION"
    RETRY = "RETRY"
    ACKNOWLEDGMENT = "ACKNOWLEDGMENT"
    ON_TEST = "ON_TEST"

@dataclass
class TelegramLogEntry:
    """Structured log entry for Telegram operations"""
    timestamp: str
    account_id: str
    phone: str
    operation: str
    status: str
    level: str
    message: str
    channel_id: Optional[str] = None
    channel_username: Optional[str] = None
    message_count: Optional[int] = None
    retry_count: Optional[int] = None
    error_code: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class TelegramMonitor:
    """Enhanced monitoring system for Telegram data collection"""
    
    def __init__(self, elastic_handler, account_id: str, phone: str):
        self.elastic_handler = elastic_handler
        self.account_id = account_id
        self.phone = phone
        self.logger = logging.getLogger(f"telegram_monitor_{account_id}")
        
    async def log_operation(self, 
                     operation: OperationType,
                     status: AccountStatus,
                     level: LogLevel,
                     message: str,
                     channel_id: Optional[str] = None,
                     channel_username: Optional[str] = None,
                     message_count: Optional[int] = None,
                     retry_count: Optional[int] = None,
                     error_code: Optional[str] = None,
                     duration_ms: Optional[int] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Log a structured operation"""
        
        log_entry = TelegramLogEntry(
            timestamp=datetime.now().isoformat(),
            account_id=self.account_id,
            phone=str(self.phone),
            operation=operation.value,
            status=status.value,
            level=level.value,
            message=message,
            channel_id=channel_id,
            channel_username=channel_username,
            message_count=message_count,
            retry_count=retry_count,
            error_code=error_code,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        # Log to console
        self.logger.info(f"[{operation.value}] {message}")
        
        # Send to Elasticsearch
        try:
            await self.elastic_handler.index_document(
                index_name="telegram-monitoring",
                document_id=f"{self.phone}_{datetime.now().timestamp()}",
                document=asdict(log_entry)
            )
        except Exception as e:
            self.logger.error(f"Failed to send log to Elasticsearch: {e}")
    
    async def log_message_collection(self, channel_id: str, channel_username: str, 
                             message_count: int, status: AccountStatus, 
                             message: str = None):
        """Log message collection operation"""
        await self.log_operation(
            operation=OperationType.MESSAGE_COLLECTION,
            status=status,
            level=LogLevel.INFO if status == AccountStatus.CONNECTED else LogLevel.ERROR,
            message=message or f"Collected {message_count} messages from {channel_username}",
            channel_id=channel_id,
            channel_username=channel_username,
            message_count=message_count
        )
    
    async def log_channel_update(self, channel_id: str, channel_username: str, 
                          status: AccountStatus, message: str = None):
        """Log channel update operation"""
        await self.log_operation(
            operation=OperationType.CHANNEL_UPDATE,
            status=status,
            level=LogLevel.INFO if status == AccountStatus.CONNECTED else LogLevel.WARNING,
            message=message or f"Updated channel {channel_username}",
            channel_id=channel_id,
            channel_username=channel_username
        )
    
    async def log_connection_status(self, status: AccountStatus, message: str = None):
        """Log connection status"""
        await self.log_operation(
            operation=OperationType.CONNECTION,
            status=status,
            level=LogLevel.INFO if status == AccountStatus.CONNECTED else LogLevel.ERROR,
            message=message or f"Account {self.phone} connection status: {status.value}"
        )
    
    async def log_retry_attempt(self, operation: str, retry_count: int, 
                         error_message: str, duration_ms: int = None):
        """Log retry attempt"""
        await self.log_operation(
            operation=OperationType.RETRY,
            status=AccountStatus.ERROR,
            level=LogLevel.WARNING,
            message=f"Retry attempt {retry_count} for {operation}: {error_message}",
            retry_count=retry_count,
            duration_ms=duration_ms,
            metadata={"operation": operation, "error": error_message}
        )
    
    async def log_acknowledgment(self, job_id: str, peer_id: str, status: str, 
                          message: str = None):
        """Log acknowledgment sent to report service"""
        await self.log_operation(
            operation=OperationType.ACKNOWLEDGMENT,
            status=AccountStatus.CONNECTED,
            level=LogLevel.INFO,
            message=message or f"Sent acknowledgment for job {job_id}, peer {peer_id}: {status}",
            metadata={"job_id": job_id, "peer_id": peer_id, "ack_status": status}
        )

# Global monitoring instances
_monitors = {}

def get_monitor(account_id: str, phone: str, elastic_handler) -> TelegramMonitor:
    """Get or create monitor instance for account"""
    key = f"{account_id}_{phone}"
    if key not in _monitors:
        _monitors[key] = TelegramMonitor(elastic_handler, account_id, phone)
    return _monitors[key]
