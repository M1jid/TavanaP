"""
Users Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import UserQueries
import schemas

from fastapi import HTTPException, status


class UsersQueriesService:
    """Service for user queries operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_users_quries(self) -> List[UserQueries]:
        """Get all users with optional disabled filter"""
        query = self.db.query(UserQueries)
        return query.all()
    
    async def get_user_quries_by_id(self, user_query_id: int) -> Optional[UserQueries]:
        """Get user query by ID"""
        return self.db.query(UserQueries).filter(UserQueries.id == user_query_id).first()
    
    async def create_user_quries(self, user_query_data: schemas.UserQueriesCreate) -> UserQueries:
        """Create a new user query"""
        
        # Create new user
        db_user_query = UserQueries(**user_query_data.dict())
        self.db.add(db_user_query)
        self.db.commit()
        self.db.refresh(db_user_query)
        return db_user_query
    
    async def update_user_quries(self, user_query: UserQueries, user_query_data: schemas.UserQueriesUpdate) -> UserQueries:
        """Update an existing user query"""
        if user_query_data is None:
            return user_query
        
        update_data = user_query_data.dict(exclude_unset=True)
                
        for field, value in update_data.items():
            if hasattr(UserQueries, field):
                setattr(user_query, field, value)
        
        self.db.commit()
        self.db.refresh(user_query)
        return user_query
    
    async def delete_user_quries(self, user_query: UserQueries) -> None:
        """Delete a user query"""
        self.db.delete(user_query)
        self.db.commit() 
