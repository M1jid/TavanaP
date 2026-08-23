"""
User Queries Pydantic Schemas
"""
from typing import List, Optional
from pydantic import Field, model_validator, BaseModel
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class BaseUserQueryIds(BaseModel):
    title: str
    description: str
    query_type: int
    must: Optional[List[str]] = Field(default_factory=list)
    should: Optional[List[str]] = Field(default_factory=list)
    must_not: Optional[List[str]] = Field(default_factory=list)
    query_string: Optional[str] = None


class UserQueries(BaseUserQueryIds):
    id: int

    model_config = {
        "from_attributes": True
    }

class UserQueriesCreate(BaseUserQueryIds):
    pass

class UserQueriesUpdate(BaseUserQueryIds):
    pass
