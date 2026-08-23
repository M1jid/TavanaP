from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any


class BaseUserChannel(BaseModel):
    chat_id: int
    interval: str
    bot_tokens: str


class AdminCreateUserChannel(BaseUserChannel):
    user_id: int
    query_id: int


class CreateUserChannel(BaseUserChannel):
    query_id: int


class UpdateUserChannel(BaseUserChannel):
    query_id: int


class UserChannel(BaseUserChannel):
    user_id: int
    query_id: int
    id: int
