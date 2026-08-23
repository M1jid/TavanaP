"""
Telegram Channels Under Follow Service
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import psycopg2

from models import TelegramChannelsUnderFollow, TelegramChannel
import schemas
from schemas.telegram_channels_underfollow import (
    TelegramChannelsUnderFollow as TelegramChannelsUnderFollowSchema
)

from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TelegramChannelsUnderFollowService:
    """Service for telegram channels under follow operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_channels_under_follow(self) -> List[TelegramChannelsUnderFollow]:
        """Get all telegram channels under follow"""
        return self.db.query(TelegramChannelsUnderFollow).all()
    
    async def get_channel_under_follow_by_id(self, id: int) -> Optional[TelegramChannelsUnderFollow]:
        """Get telegram channel under follow by ID"""
        return self.db.query(TelegramChannelsUnderFollow).filter(TelegramChannelsUnderFollow.id == id).first()
    
    async def get_channel_under_follow_by_channel_id(self, channel_id: int) -> Optional[TelegramChannelsUnderFollow]:
        """Get telegram channel under follow by channel ID"""
        return self.db.query(TelegramChannelsUnderFollow).filter(
            TelegramChannelsUnderFollow.channel_id == channel_id
        ).first()
    
    async def get_channels_under_follow_with_details(self) -> List[Dict[str, Any]]:
        """Get all channels under follow with their complete TelegramChannel details"""
        channels_under_follow = self.db.query(TelegramChannelsUnderFollow).all()
        result = []
        
        for follow_entry in channels_under_follow:
            # Get the complete TelegramChannel details
            channel_details = self.db.query(TelegramChannel).filter(
                TelegramChannel.chat_id == follow_entry.channel_id
            ).first()
            
            if channel_details:
                # Combine follow entry data with channel details
                entry_data = TelegramChannelsUnderFollowSchema.model_validate(follow_entry, from_attributes=True)
                channel_data = schemas.TelegramChannelSchema.model_validate(channel_details, from_attributes=True)
                
                result.append({
                    "follow_entry": entry_data.model_dump(),
                    "channel_details": channel_data.model_dump()
                })
        
        return result
    
    async def create_channel_under_follow(self, channel_data) -> TelegramChannelsUnderFollow:
        """Create a new telegram channel under follow"""
        # Validate channel_id
        if channel_data.channel_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="channel_id must be a positive integer"
            )
        
        # Check if the channel exists in telegram_channels table
        existing_channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.chat_id == channel_data.channel_id
        ).first()
        if not existing_channel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel with id {channel_data.channel_id} does not exist in telegram_channels table"
            )
        
        # Check if this channel is already in under_follow
        existing_under_follow = self.db.query(TelegramChannelsUnderFollow).filter(
            TelegramChannelsUnderFollow.channel_id == channel_data.channel_id
        ).first()
        if existing_under_follow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel with id {channel_data.channel_id} is already in under_follow"
            )
        
        try:
            channel_model = TelegramChannelsUnderFollow(**channel_data.model_dump())
            self.db.add(channel_model)
            self.db.commit()
            self.db.refresh(channel_model)
            return channel_model
        except IntegrityError as e:
            self.db.rollback()
            if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Channel with id {channel_data.channel_id} does not exist in telegram_channels table"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This record violates a unique constraint in the database"
            )
    
    async def update_channel_under_follow(
        self,
        channel_data,
        channel: TelegramChannelsUnderFollow
    ) -> TelegramChannelsUnderFollow:
        """Update a telegram channel under follow"""
        # Validate channel_id if it's being updated
        if channel_data.channel_id is not None:
            if channel_data.channel_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="channel_id must be a positive integer"
                )
            
            # Check if the new channel exists in telegram_channels table
            existing_channel = self.db.query(TelegramChannel).filter(
                TelegramChannel.chat_id == channel_data.channel_id
            ).first()
            if not existing_channel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Channel with id {channel_data.channel_id} does not exist in telegram_channels table"
                )
            
            # Check if the new channel is already in under_follow (excluding current record)
            existing_under_follow = self.db.query(TelegramChannelsUnderFollow).filter(
                TelegramChannelsUnderFollow.channel_id == channel_data.channel_id,
                TelegramChannelsUnderFollow.id != channel.id
            ).first()
            if existing_under_follow:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Channel with id {channel_data.channel_id} is already in under_follow"
                )
        
        # Update the model with new data
        update_data = channel_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(channel, field, value)
        
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    async def delete_channel_under_follow(self, channel: TelegramChannelsUnderFollow):
        """Delete a telegram channel under follow"""
        self.db.delete(channel)
        self.db.commit()
    
    async def delete_channel_under_follow_by_channel_id(self, channel: TelegramChannelsUnderFollow):
        """Delete a telegram channel under follow by channel ID"""
        channel_model = self.db.query(TelegramChannelsUnderFollow).filter(
            TelegramChannelsUnderFollow.channel_id == channel.channel_id
        ).first()
        if channel_model:
            self.db.delete(channel_model)
            self.db.commit() 