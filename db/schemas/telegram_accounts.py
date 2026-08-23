"""
Telegram Accounts Pydantic Schemas
"""

from typing import List, Optional
from pydantic import Field
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class TelegramAccount(BaseSchema):
    """Telegram account schema for responses"""
    id: int
    phone: int
    api_id: int
    api_hash: str
    session_file: str
    process: int
    roles: List[str]


class TelegramAccountCreate(BaseCreateSchema):
    """Telegram account schema for creation"""
    phone: int
    api_id: int
    api_hash: str = Field(..., max_length=100)
    session_file: str = Field(..., max_length=100)
    process: int = 0
    roles: List[str]


class TelegramAccountUpdate(BaseUpdateSchema):
    """Telegram account schema for updates"""
    phone: Optional[int] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = Field(None, max_length=100)
    session_file: Optional[str] = Field(None, max_length=100)
    process: Optional[int] = None 
    roles: Optional[List[str]] = None
