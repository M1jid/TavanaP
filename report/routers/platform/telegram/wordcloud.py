from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta
from typing import List

from auth.auth import get_current_active_user, User
from schemas import telegram_schemas as schemas
from services import services
from services.platform.telegram import wordcloud

router = APIRouter(prefix="/wordcloud", tags=["Telegram Wordcloud"])


@router.get(
    "",
    summary="Get Telegram wordcloud",
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_channel_details.md'),
)
async def get_wordcloud(
    search_text: str = Query(default="", example="تورم", description="Title of the trend"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    selected_channels: List[int] = Query(default=[], example=[], description="Selected channel Peer IDs"),    # filters: schemas.TelegramWordcloudFilter,
    # current_user: User = Depends(get_current_active_user),
):
    """Generate wordcloud data from Telegram messages"""
    perm = "platform.telegram.fa.wordcloud"
    # services.check_access(user=current_user, permission=perm)
    return await wordcloud.get_wordcloud(search_text, start_date, end_date, selected_channels)


@router.get(
    "/owned_channels",
    summary="Get Telegram wordcloud",
    # description=services.load_description('docs/descriptions/api_v1_platform_telegram_channel_details.md'),
)
async def get_owned_channels_wordcloud(
    channel_id: int = Query(..., description="Channel ID"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    # current_user: User = Depends(get_current_active_user),
):
    """Generate wordcloud data from Telegram messages"""
    perm = "platform.telegram.fa.wordcloud"
    # services.check_access(user=current_user, permission=perm)
    return await wordcloud.get_owned_channels_wordcloud(channel_id, start_date, end_date)


@router.get(
    "/user",
    summary="Get Telegram wordcloud of User",
)
async def get_user_wordcloud(
    user_id: int = Query(..., description="User ID"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    # current_user: User = Depends(get_current_active_user),
):
    """Generate wordcloud data from Telegram messages"""
    perm = "platform.telegram.fa.wordcloud"
    # services.check_access(user=current_user, permission=perm)
    return await wordcloud.get_user_wordcloud(user_id, start_date, end_date)


@router.get(
    "/channel",
    summary="Get Telegram wordcloud of Channel",
)
async def get_channel_wordcloud(
    channel_id: int = Query(..., description="Channel ID"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    # current_user: User = Depends(get_current_active_user),
):
    """Generate wordcloud data from Telegram messages"""
    perm = "platform.telegram.fa.wordcloud"
    # services.check_access(user=current_user, permission=perm)
    return await wordcloud.get_channel_wordcloud(channel_id, start_date, end_date)

@router.get(
    "/group",
    summary="Get Telegram wordcloud of Group",
)
async def get_group_wordcloud(
    group_id: int = Query(..., description="Group ID"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    # current_user: User = Depends(get_current_active_user),
):
    """Generate wordcloud data from Telegram messages"""
    perm = "platform.telegram.fa.wordcloud"
    # services.check_access(user=current_user, permission=perm)
    return await wordcloud.get_group_wordcloud(group_id, start_date, end_date)
