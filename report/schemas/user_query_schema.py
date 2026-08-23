from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any


class QueryClause(BaseModel):
    must: List[str]
    should: List[str]
    must_not: List[str]


class BaseUserQuery(BaseModel):
    raw_query: List[QueryClause]


class AdminCreateUserQuery(BaseUserQuery):
    user_id: int


class CreateUserQuery(BaseUserQuery):
    pass


class UpdateUserQuery(BaseUserQuery):
    query: Dict[str, Any]


class UserQuery(BaseUserQuery):
    user_id: int
    query: Dict[str, Any]
    id: int
