"""
Telegram Users Under Follow Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import psycopg2

from models import TelegramUsersUnderFollow
from schemas.telegram_users_underfollow import (
    TelegramUsersUnderFollow as TelegramUsersUnderFollowSchema
)

from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TelegramUsersUnderFollowService:
    """Service for telegram users under follow operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_users_under_follow(self) -> List[TelegramUsersUnderFollow]:
        """Get all telegram users under follow"""
        return self.db.query(TelegramUsersUnderFollow).all()
    
    async def get_user_under_follow_by_id(self, id: int) -> Optional[TelegramUsersUnderFollow]:
        """Get telegram user under follow by ID"""
        return self.db.query(TelegramUsersUnderFollow).filter(TelegramUsersUnderFollow.id == id).first()
    
    async def get_user_under_follow_by_user_id(self, user_id: int) -> Optional[TelegramUsersUnderFollow]:
        """Get telegram user under follow by user ID"""
        return self.db.query(TelegramUsersUnderFollow).filter(
            TelegramUsersUnderFollow.user_id == user_id
        ).first()
    
    async def create_user_under_follow(self, user_data) -> TelegramUsersUnderFollow:
        """Create a new telegram user under follow"""
        # Validate user_id
        if user_data.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id must be a positive integer"
            )
        
        # Check if this user is already in under_follow
        existing_under_follow = self.db.query(TelegramUsersUnderFollow).filter(
            TelegramUsersUnderFollow.user_id == user_data.user_id
        ).first()
        if existing_under_follow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {user_data.user_id} is already in under_follow"
            )
        
        try:
            user_model = TelegramUsersUnderFollow(**user_data.model_dump())
            self.db.add(user_model)
            self.db.commit()
            self.db.refresh(user_model)
            return user_model
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This record violates a unique constraint in the database"
            )
    
    async def update_user_under_follow(
        self,
        user_data,
        user: TelegramUsersUnderFollow
    ) -> TelegramUsersUnderFollow:
        """Update a telegram user under follow"""
        # Validate user_id if it's being updated
        if user_data.user_id is not None:
            if user_data.user_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id must be a positive integer"
                )
            
            # Check if the new user is already in under_follow (excluding current record)
            existing_under_follow = self.db.query(TelegramUsersUnderFollow).filter(
                TelegramUsersUnderFollow.user_id == user_data.user_id,
                TelegramUsersUnderFollow.id != user.id
            ).first()
            if existing_under_follow:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with id {user_data.user_id} is already in under_follow"
                )
        
        # Update the model with new data
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete_user_under_follow(self, user: TelegramUsersUnderFollow):
        """Delete a telegram user under follow"""
        self.db.delete(user)
        self.db.commit()
    
    async def delete_user_under_follow_by_user_id(self, user: TelegramUsersUnderFollow):
        """Delete a telegram user under follow by user ID"""
        user_model = self.db.query(TelegramUsersUnderFollow).filter(
            TelegramUsersUnderFollow.user_id == user.user_id
        ).first()
        if user_model:
            self.db.delete(user_model)
            self.db.commit() 