from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict
from datetime import date
from enum import Enum


class QueryClause(BaseModel):
    must: List[str] = Field(default_factory=list)
    must_not: List[str] = Field(default_factory=list)
    should: List[str] = Field(default_factory=list)


class UserQuery(BaseModel):
    query: List[QueryClause] = Field(
        ...,
        example=[
            {
                "must": ["والیبال"],
                "must_not": ["شکست", "باخت", "حذف"],
                "should": ["ایران", "کشورمون"]
            }
        ],
        description="Each query clause must only contain 'must', 'must_not', and 'should' as keys, and their values must be lists of strings."
    )


class UpdateUserQuery(UserQuery):
    id: int
    user_id: int


class CreateUserQuery(UserQuery):
    user_id: int
