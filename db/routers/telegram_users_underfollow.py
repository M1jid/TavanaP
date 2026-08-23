"""
Telegram Users Under Follow API Router
"""
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from services.telegram_users_underfollow import TelegramUsersUnderFollowService
from schemas.telegram_users_underfollow import (
    TelegramUsersUnderFollow,
    TelegramUsersUnderFollowCreate,
    TelegramUsersUnderFollowUpdate
)

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/users/underfollow/all",
    response_model=List[TelegramUsersUnderFollow],
    summary="Get all telegram users under follow",
    description="Get all telegram users under follow",
    tags=['Telegram Users Under Follow']
)
async def get_telegram_users_under_follow_all(
    db: Session = Depends(get_db)
):
    """Get all telegram users under follow"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        return await service.get_all_users_under_follow()


@router.get(
    "/users/underfollow/{id}",
    response_model=TelegramUsersUnderFollow,
    summary="Get telegram user under follow by ID",
    description="Get a specific telegram user under follow by its ID",
    tags=['Telegram Users Under Follow']
)
async def get_telegram_users_under_follow_id(
    id: int,
    db: Session = Depends(get_db)
):
    """Get telegram user under follow by ID"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        user = await service.get_user_under_follow_by_id(id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User under follow does not exist"
            )
        return user


@router.get(
    "/users/underfollow/user/{user_id}",
    response_model=TelegramUsersUnderFollow,
    summary="Get telegram user under follow by user ID",
    description="Get a specific telegram user under follow by its user ID",
    tags=['Telegram Users Under Follow']
)
async def get_telegram_users_under_follow_user_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get telegram user under follow by user ID"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        user = await service.get_user_under_follow_by_user_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User under follow does not exist"
            )
        return user


@router.post(
    "/users/underfollow",
    response_model=TelegramUsersUnderFollow,
    summary="Create telegram user under follow",
    description="Create a new telegram user under follow",
    tags=['Telegram Users Under Follow']
)
async def create_telegram_users_under_follow(
    user_data: TelegramUsersUnderFollowCreate,
    db: Session = Depends(get_db)
):
    """Create a new telegram user under follow"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        return await service.create_user_under_follow(user_data)


@router.delete(
    "/users/underfollow/{id}",
    summary="Delete telegram user under follow by ID",
    description="Delete a specific telegram user under follow by its ID",
    tags=['Telegram Users Under Follow']
)
async def delete_telegram_users_under_follow(
    id: int,
    db: Session = Depends(get_db)
):
    """Delete telegram user under follow by ID"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        user = await service.get_user_under_follow_by_id(id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User under follow does not exist"
            )
        
        await service.delete_user_under_follow(user)
        return "Successfully deleted the user under follow"


@router.delete(
    "/users/underfollow/user/{user_id}",
    summary="Delete telegram user under follow by user ID",
    description="Delete a specific telegram user under follow by its user ID",
    tags=['Telegram Users Under Follow']
)
async def delete_telegram_users_under_follow_user_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete telegram user under follow by user ID"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        user = await service.get_user_under_follow_by_user_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User under follow does not exist"
            )
        
        await service.delete_user_under_follow_by_user_id(user)
        return "Successfully deleted the user under follow"


@router.put(
    "/users/underfollow/{id}",
    response_model=TelegramUsersUnderFollow,
    summary="Update telegram user under follow",
    description="Update a specific telegram user under follow by its ID",
    tags=['Telegram Users Under Follow']
)
async def update_telegram_users_under_follow(
    id: int,
    user_data: TelegramUsersUnderFollowUpdate,
    db: Session = Depends(get_db)
):
    """Update telegram user under follow"""
    async with db_lock:
        service = TelegramUsersUnderFollowService(db)
        user = await service.get_user_under_follow_by_id(id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User under follow does not exist"
            )
        
        return await service.update_user_under_follow(user_data, user) 