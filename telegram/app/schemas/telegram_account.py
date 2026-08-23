from pydantic import BaseModel, model_validator
from typing import Optional, List


class TelegramSchemaBaseAccount(BaseModel):
    phone: int
    api_id: int
    api_hash: str
    session_file: str
    process: int
    roles: List[str]


class TelegramSchemaResponseAccount(TelegramSchemaBaseAccount):
    id: int


class TelegramSchemaCreateAccount(BaseModel):
    phone: int
    api_id: int
    api_hash: str
    session_file: str
    process: int
    roles: List[str]


class TelegramSchemaUpdateAccount(BaseModel):
    phone: Optional[int] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_file: Optional[str] = None
    process: Optional[int] = None
    roles: Optional[List[str]] = None
