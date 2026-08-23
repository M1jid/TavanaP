"""
RSS Resources Pydantic Schemas
"""
from typing import Optional
from pydantic import Field
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema
from datetime import datetime


class RSSResource(BaseSchema):
    """RSS resource schema for responses"""
    id: int
    key: str
    value_rss: str
    blocked: bool
    last_update: datetime
    
    class Config:
        from_attributes = True

class RSSResourceCreate(BaseCreateSchema):
    """RSS resource schema for creation"""
    key: str = Field(..., max_length=100)
    value_rss: str = Field(..., max_length=100)
    blocked: Optional[bool] = False


class RSSResourceUpdate(BaseUpdateSchema):
    """RSS resource schema for updates"""
    key: Optional[str] = None
    value_rss: Optional[str] = None
    blocked: Optional[bool] = False
    last_update: Optional[datetime] = None
