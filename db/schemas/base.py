"""
Base Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class BaseCreateSchema(BaseSchema):
    """Base schema for create operations"""
    pass


class BaseUpdateSchema(BaseSchema):
    """Base schema for update operations"""
    pass 