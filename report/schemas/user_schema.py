from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, UTC
from typing import Optional, List, Dict


class BaseUser(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    disabled: Optional[bool] = False
    history: List[Dict] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class CreateUser(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    disabled: Optional[bool] = False
    permissions: List[str] = Field(default_factory=list)
    password: str


class RegularUpdateUser(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class RootUpdateUser(RegularUpdateUser):
    disabled: Optional[bool] = None
    history: Optional[List[Dict]] = None
    permissions: Optional[List[str]] = None
    query_ids: Optional[List[int]] = None


class User(BaseUser):
    hashed_password: str
    id: int
