"""
Telegram Channels Under Follow Pydantic Schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import Field
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class BaseTelegramChannelsUnderFollow(BaseSchema):
    """Base schema for Telegram Channels Under Follow"""
    channel_id: int = Field(..., gt=0, description="Must be a positive integer referencing an existing telegram channel")
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None


class TelegramChannelsUnderFollow(BaseTelegramChannelsUnderFollow):
    """Schema for Telegram Channels Under Follow with ID"""
    id: int


class TelegramChannelsUnderFollowCreate(BaseCreateSchema):
    """Schema for creating Telegram Channels Under Follow"""
    channel_id: int = Field(..., gt=0, description="Must be a positive integer referencing an existing telegram channel")
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    notes: Optional[str] = None


class TelegramChannelsUnderFollowUpdate(BaseUpdateSchema):
    """Schema for updating Telegram Channels Under Follow"""
    channel_id: Optional[int] = Field(None, gt=0, description="Must be a positive integer referencing an existing telegram channel")
    added_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    notes: Optional[str] = None 