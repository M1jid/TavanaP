"""
Telegram Channels Under Follow API Router
"""
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from services.telegram_channels_underfollow import TelegramChannelsUnderFollowService
from schemas.telegram_channels_underfollow import (
    TelegramChannelsUnderFollow,
    TelegramChannelsUnderFollowCreate,
    TelegramChannelsUnderFollowUpdate
)

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/channels/underfollow/all",
    response_model=List[TelegramChannelsUnderFollow],
    summary="Get all telegram channels under follow",
    description="Get all telegram channels under follow",
    tags=['Telegram Channels Under Follow']
)
async def get_telegram_channels_under_follow_all(
    db: Session = Depends(get_db)
):
    """Get all telegram channels under follow"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        return await service.get_all_channels_under_follow()


@router.get(
    "/channels/underfollow/details/all",
    summary="Get all telegram channels under follow with details",
    description="Get all telegram channels under follow with their complete channel details",
    tags=['Telegram Channels Under Follow']
)
async def get_telegram_channels_under_follow_with_details(
    db: Session = Depends(get_db)
):
    """Get all telegram channels under follow with details"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        return await service.get_channels_under_follow_with_details()


@router.get(
    "/channels/underfollow/{id}",
    response_model=TelegramChannelsUnderFollow,
    summary="Get telegram channel under follow by ID",
    description="Get a specific telegram channel under follow by its ID",
    tags=['Telegram Channels Under Follow']
)
async def get_telegram_channels_under_follow_id(
    id: int,
    db: Session = Depends(get_db)
):
    """Get telegram channel under follow by ID"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        channel = await service.get_channel_under_follow_by_id(id)
        if channel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel under follow does not exist"
            )
        return channel


@router.get(
    "/channels/underfollow/channel/{channel_id}",
    response_model=TelegramChannelsUnderFollow,
    summary="Get telegram channel under follow by channel ID",
    description="Get a specific telegram channel under follow by its channel ID",
    tags=['Telegram Channels Under Follow']
)
async def get_telegram_channels_under_follow_channel_id(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Get telegram channel under follow by channel ID"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        channel = await service.get_channel_under_follow_by_channel_id(channel_id)
        if channel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel under follow does not exist"
            )
        return channel


@router.post(
    "/channels/underfollow",
    response_model=TelegramChannelsUnderFollow,
    summary="Create telegram channel under follow",
    description="Create a new telegram channel under follow",
    tags=['Telegram Channels Under Follow']
)
async def create_telegram_channels_under_follow(
    channel_data: TelegramChannelsUnderFollowCreate,
    db: Session = Depends(get_db)
):
    """Create a new telegram channel under follow"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        return await service.create_channel_under_follow(channel_data)


@router.delete(
    "/channels/underfollow/{id}",
    summary="Delete telegram channel under follow by ID",
    description="Delete a specific telegram channel under follow by its ID",
    tags=['Telegram Channels Under Follow']
)
async def delete_telegram_channels_under_follow(
    id: int,
    db: Session = Depends(get_db)
):
    """Delete telegram channel under follow by ID"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        channel = await service.get_channel_under_follow_by_id(id)
        if channel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel under follow does not exist"
            )
        
        await service.delete_channel_under_follow(channel)
        return "Successfully deleted the channel under follow"


@router.delete(
    "/channels/underfollow/channel/{channel_id}",
    summary="Delete telegram channel under follow by channel ID",
    description="Delete a specific telegram channel under follow by its channel ID",
    tags=['Telegram Channels Under Follow']
)
async def delete_telegram_channels_under_follow_channel_id(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Delete telegram channel under follow by channel ID"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        channel = await service.get_channel_under_follow_by_channel_id(channel_id)
        if channel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel under follow does not exist"
            )
        
        await service.delete_channel_under_follow_by_channel_id(channel)
        return "Successfully deleted the channel under follow"


@router.put(
    "/channels/underfollow/{id}",
    response_model=TelegramChannelsUnderFollow,
    summary="Update telegram channel under follow",
    description="Update a specific telegram channel under follow by its ID",
    tags=['Telegram Channels Under Follow']
)
async def update_telegram_channels_under_follow(
    id: int,
    channel_data: TelegramChannelsUnderFollowUpdate,
    db: Session = Depends(get_db)
):
    """Update telegram channel under follow"""
    async with db_lock:
        service = TelegramChannelsUnderFollowService(db)
        channel = await service.get_channel_under_follow_by_id(id)
        if channel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel under follow does not exist"
            )
        
        return await service.update_channel_under_follow(channel_data, channel) 