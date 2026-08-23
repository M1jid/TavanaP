"""
User Pydantic Schemas
"""
from typing import List, Optional
from pydantic import EmailStr, Field
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class User(BaseSchema):
    """User schema for responses"""
    id: int
    username: str
    full_name: str
    email: EmailStr
    hashed_password: str
    disabled: bool = False
    permissions: List[str] = []
    history: List[dict] = []

    query_ids: List[int] = []
    following_channels: List[int] = []
    following_groups: List[int] = []
    following_users: List[int] = []
    accessible_urls: List[str] = []


class UserCreate(BaseCreateSchema):
    """User schema for creation"""
    username: str = Field(..., min_length=1, max_length=32)
    full_name: str = Field(..., min_length=1, max_length=32)
    email: EmailStr
    hashed_password: str = Field(..., min_length=1)
    disabled: bool = False
    permissions: List[str] = []
    history: List[dict] = []

    query_ids: List[int] = []
    following_channels: Optional[List[int]] = []
    following_groups: Optional[List[int]] = []
    following_users: Optional[List[int]] = []
    accessible_urls: Optional[List[str]] = []


class UserUpdate(BaseUpdateSchema):
    """User schema for updates"""
    username: Optional[str] = Field(None, min_length=1, max_length=32)
    full_name: Optional[str] = Field(None, min_length=1, max_length=32)
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = Field(None, min_length=1)
    disabled: Optional[bool] = None
    permissions: Optional[List[str]] = None
    history: Optional[List[dict]] = None

    query_ids: Optional[List[int]] = None 
    following_channels: Optional[List[int]] = None
    following_groups: Optional[List[int]] = None
    following_users: Optional[List[int]] = None
    accessible_urls: Optional[List[str]] = None
