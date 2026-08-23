"""
Telegram Users Under Follow Pydantic Schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import Field
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class BaseTelegramUsersUnderFollow(BaseSchema):
    """Base schema for Telegram Users Under Follow"""
    user_id: int = Field(..., gt=0, description="Must be a positive integer")
    username: Optional[str] = None
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None


class TelegramUsersUnderFollow(BaseTelegramUsersUnderFollow):
    """Schema for Telegram Users Under Follow with ID"""
    id: int


class TelegramUsersUnderFollowCreate(BaseCreateSchema):
    """Schema for creating Telegram Users Under Follow"""
    user_id: int = Field(..., gt=0, description="Must be a positive integer")
    username: Optional[str] = None
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None


class TelegramUsersUnderFollowUpdate(BaseUpdateSchema):
    """Schema for updating Telegram Users Under Follow"""
    user_id: Optional[int] = Field(None, gt=0, description="Must be a positive integer")
    username: Optional[str] = None
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    notes: Optional[str] = None 