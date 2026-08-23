from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from typing import Optional, List
import logging
from datetime import date, timedelta

from auth.auth import get_current_active_user, User
from services import services
from services.platform.telegram.shared_services import TelegramService
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config
from services.platform.telegram import groups as groups_service
from utils import db_handler as db

# Logging
logger = logging.getLogger(__name__)

# Initialize MinIO handler
minio_config = get_minio_config(type='group')
minio_handler = MinIOHandler(**minio_config)

router = APIRouter(prefix="/groups")


@router.get(
    "/list",
    tags=["Telegram Groups"],
    summary="List of Telegram Groups"
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_channels_list.md'),
)
async def get_groups_list(
    size: int = Query(10, description="Number of results to return"),
    scroll_id: Optional[str] = Query(None, description="Pagination cursor"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of Telegram groups with optional search and pagination"""
    perm = "platform.telegram.fa.groups.list"
    services.check_access(user=current_user, permission=perm)
    
    return await groups_service.get_groups_list(size, scroll_id, search)


@router.get(
    "/underfollow/all",
    tags=["Telegram Groups Underfollow"],
    summary="Get Telegram groups under follow"
    # response_model=List[schemas.TelegramChannelsUnderFollow],
)
async def get_groups_underfollow(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram groups under follow"""
    perm = "platform.telegram.fa.groups.underfollow"
    services.check_access(user=current_user, permission=perm)
    return [{'id': peer_id} for peer_id in current_user.following_groups]


@router.get(
    "/underfollow/status/{group_id}",
    tags=["Telegram Groups Underfollow"],
    summary="Get Telegram groups under follow"
)
async def get_groups_underfollow_status(
    group_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram groups under follow"""
    perm = "platform.telegram.fa.groups.underfollow"
    services.check_access(user=current_user, permission=perm)
    return group_id in current_user.following_groups


@router.get(
    "/underfollow/details/all",
    tags=["Telegram Groups Underfollow"],
    summary="Get Telegram groups under follow details"
)
async def get_groups_underfollow_details(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram groups under follow"""
    perm = "platform.telegram.fa.groups.underfollow"
    services.check_access(user=current_user, permission=perm)
    return await groups_service.get_groups_underfollow_details(current_user.following_groups)


@router.delete(
    "/underfollow/{group_id}",
    tags=["Telegram Groups Underfollow"],
    summary="Delete Telegram group under follow"
)
async def delete_group_underfollow(
    group_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete Telegram group under follow"""
    perm = "platform.telegram.fa.groups.underfollow"
    services.check_access(user=current_user, permission=perm)
    if group_id not in current_user.following_groups:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group not under follow")

    current_user.following_groups.remove(group_id)
    db.update_user(current_user.id, current_user.model_dump())
    return await groups_service.get_groups_underfollow_details(following_groups=[group_id])


@router.post(
    "/underfollow/{group_id}",
    tags=["Telegram Groups Underfollow"],
    summary="Create Telegram group under follow"
    # response_model=schemas.TelegramChannelsUnderFollow,
)
async def create_group_underfollow(
    group_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Create Telegram group under follow"""
    perm = "platform.telegram.fa.groups.underfollow"
    services.check_access(user=current_user, permission=perm)
    if group_id in current_user.following_groups:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group already under follow")

    try:
        _ = db.get_telegram_peer(peer_id=group_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    current_user.following_groups.append(group_id)
    db.update_user(current_user.id, current_user.model_dump())
    return await groups_service.get_groups_underfollow_details(following_groups=[group_id])


@router.get(
    "/details/{group_id}",
    tags=["Telegram Groups"],
    summary="Get Telegram Group Details",
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_group_details.md'),
)
async def get_group_details(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed information about a specific Telegram group"""
    perm = "platform.telegram.fa.groups.details"
    services.check_access(user=current_user, permission=perm)
    
    return await groups_service.get_group_details(group_id)

@router.get(
    "/details/overview/{group_id}",
    tags=["Telegram Groups"],
    summary="Get Telegram Group Details",
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_group_details.md'),
)
async def get_group_details_overview(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed information about a specific Telegram group"""
    perm = "platform.telegram.fa.groups.details"
    services.check_access(user=current_user, permission=perm)
    
    return await groups_service.get_group_details_overview(group_id)

@router.post(
    "/upload-image/{group_id}",
    tags=["Telegram Groups"],
    summary="Upload Group Image",
    description="Upload a profile image for a specific Telegram group"
)
async def upload_group_image(
    group_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a profile image for a specific Telegram group"""
    perm = "platform.telegram.fa.groups.upload.image"
    services.check_access(user=current_user, permission=perm)

    return await TelegramService.upload_group_image(group_id, file)


@router.get("/messages",
    summary="Get Telegram group messages",
    tags=["Telegram Groups"],
)
async def get_group_messages(
    size: int = Query(default=12, example=12, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    selected_groups: List[int] = Query(default=[], example=[], description="List of group IDs to get messages for"),
    start_date: str = Query(default=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    search_text: str = Query("", description="Search text"),
    sentiment: str = Query(default="", example="", description="Sentiment: خنثی, مثبت, منفی"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram group messages based on filters"""
    perm = "platform.telegram.fa.groups.messages"
    services.check_access(user=current_user, permission=perm)
    
    if not search_text:
        search_text = ''
    if not start_date:
        start_date = default=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    return await groups_service.get_group_messages(size, page, selected_groups, start_date, end_date, search_text, sentiment)
