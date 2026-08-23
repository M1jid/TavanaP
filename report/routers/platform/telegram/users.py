from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from typing import Optional, List
from datetime import date, timedelta
import logging

from auth.auth import get_current_active_user, User
from schemas import telegram_schemas as schemas
from services import services
from services.platform.telegram import users as users_service
from services.platform.telegram.shared_services import TelegramService
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config
from utils import db_handler as db

# Initialize MinIO handler
minio_config = get_minio_config(type='channel')
minio_handler = MinIOHandler(**minio_config)

# Logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users")

user_image_bucket = 'telegram-images-users'


@router.get(
    "/list",
    tags=["Telegram Users"],
    summary="List of Telegram Users"
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_channels_list.md'),
)
async def get_users_list(
    size: int = Query(10, description="Number of results to return"),
    scroll_id: Optional[str] = Query(None, description="Pagination cursor"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of Telegram users with optional search and pagination"""
    perm = "platform.telegram.fa.users.list"
    services.check_access(user=current_user, permission=perm)
    
    return await users_service.get_users_list(size, scroll_id, search)


@router.get(
    "/underfollow/all",
    tags=["Telegram Users Underfollow"],
    summary="Get Telegram users under follow"
    # response_model=List[schemas.TelegramChannelsUnderFollow],
)
async def get_users_underfollow(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram users under follow"""
    perm = "platform.telegram.fa.users.underfollow"
    services.check_access(user=current_user, permission=perm)
    return [{'id': peer_id} for peer_id in current_user.following_users]


@router.get(
    "/underfollow/status/{user_id}",
    tags=["Telegram Users Underfollow"],
    summary="Get Telegram users under follow"
)
async def get_users_underfollow_status(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram users under follow"""
    perm = "platform.telegram.fa.users.underfollow"
    services.check_access(user=current_user, permission=perm)
    return user_id in current_user.following_users


@router.get(
    "/underfollow/details/all",
    tags=["Telegram Users Underfollow"],
    summary="Get Telegram groups under follow details"
)
async def get_users_underfollow_details(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram users under follow"""
    perm = "platform.telegram.fa.users.underfollow"
    services.check_access(user=current_user, permission=perm)
    return await users_service.get_users_underfollow_details(current_user.following_users)


@router.delete(
    "/underfollow/{user_id}",
    tags=["Telegram Users Underfollow"],
    summary="Delete Telegram user under follow"
)
async def delete_user_underfollow(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete Telegram user under follow"""
    perm = "platform.telegram.fa.users.underfollow"
    services.check_access(user=current_user, permission=perm)
    if user_id not in current_user.following_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not under follow")

    current_user.following_users.remove(user_id)
    db.update_user(current_user.id, current_user.model_dump())
    return await users_service.get_users_underfollow_details(following_users=[user_id])


@router.post(
    "/underfollow/{user_id}",
    tags=["Telegram Users Underfollow"],
    summary="Create Telegram user under follow"
    # response_model=schemas.TelegramChannelsUnderFollow,
)
async def create_user_underfollow(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Create Telegram user under follow"""
    perm = "platform.telegram.fa.users.underfollow"
    services.check_access(user=current_user, permission=perm)
    if user_id in current_user.following_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already under follow")

    current_user.following_users.append(user_id)
    db.update_user(current_user.id, current_user.model_dump())
    return await users_service.get_users_underfollow_details(following_users=[user_id])


@router.get(
    "/details/{user_id}",
    tags=["Telegram Users"],
    summary="Get details of a Telegram user",
)
async def get_user_details(
    user_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a Telegram user"""
    perm = "platform.telegram.fa.users.details"
    services.check_access(user=current_user, permission=perm)

    return await users_service.get_user_details(user_id)

@router.get(
    "/details/overview/{user_id}",
    tags=["Telegram Users"],
    summary="Get details of a Telegram user",
)
async def get_user_details_overview(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a Telegram user"""
    perm = "platform.telegram.fa.users.details"
    services.check_access(user=current_user, permission=perm)
    return await users_service.get_user_details_overview(user_id)

@router.get(
    "/messages",
    tags=["Telegram Users"],
    summary="List of Telegram Messages written by a user",
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_channels_list.md'),
)
async def get_user_messages(
    size: int = Query(default=12, example=12, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    selected_users: List[int] = Query(default=[], example=[], description="List of user IDs to get comments for"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    search_text: str = Query(default="", description="Search text"),
    sentiment: str = Query(default="", description="Sentiment: خنثی, مثبت, منفی"),
    current_user: User = Depends(get_current_active_user),
):
    """Get list of Telegram messages written by a user with optional search and pagination"""
    perm = "platform.telegram.fa.users.messages"
    services.check_access(user=current_user, permission=perm)

    return await users_service.get_user_messages(size, page, selected_users, start_date, end_date, search_text, sentiment)
    
@router.get(
    "/messages/details/{private_url:path}",
    tags=["Telegram Users"],
    summary="Get Telegram message details",
    response_model=schemas.TelegramCommentDetails,
    # description=services.load_description('docs/platform/telegram/get_telegram_message_details.md'),
)
async def get_message_details(
    private_url: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get Telegram message details"""
    perm = "platform.telegram.fa.users.messages"
    services.check_access(user=current_user, permission=perm)

    return await users_service.get_messages_details(private_url)

@router.post(
    "/upload-image/{user_id}",
    tags=["Telegram Users"],
    summary="Upload User Image",
    description="Upload a profile image for a specific Telegram user"
)
async def upload_user_image(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a profile image for a specific Telegram user"""
    perm = "platform.telegram.fa.users.upload.image"
    services.check_access(user=current_user, permission=perm)

    return await TelegramService.upload_user_image(user_id, file)

@router.get(
    "/joinedchannels",
    tags=["Telegram Users"],
    summary="Get Telegram users joined channels",
)
async def get_user_joined_channels(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get Telegram users joined channels"""
    perm = "platform.telegram.fa.users.joinedchannels"
    services.check_access(user=current_user, permission=perm)

    return await users_service.get_user_joined_channels(user_id)
