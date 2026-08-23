from fastapi import APIRouter, Depends
from fastapi import Query

from datetime import date, timedelta

from auth.auth import get_current_active_user, User
from services.platform.telegram import trends as trends_service
from services import services


router = APIRouter(prefix="/trends", tags=["Telegram Trends"])


@router.get("/title", summary="Get top Telegram trends based on title", description=services.load_description('docs/descriptions/api_v1_platform_telegram_trends.md'))
async def get_trends_title(
    title: str = Query(default="تورم", example="تورم", description="Title of the trend"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    sort: str = Query(default="DATE", example="DATE", description="Sort by"),
    # current_user: User = Depends(get_current_active_user),
):
    """Get top Telegram trends based on title"""
    perm = "platform.telegram.fa.trends.title"
    # services.check_access(user=current_user, permission=perm)
    
    return await trends_service.get_trends_title(title, start_date, end_date, sort)

@router.get("/overview", summary="Get top Telegram trends overview", description=services.load_description('docs/descriptions/api_v1_platform_telegram_trends.md'))
async def get_trends_overview(
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    sort: str = Query(default="DATE", example="DATE", description="Sort by"),
    # current_user: User = Depends(get_current_active_user),
):
    """Get top Telegram trends overview"""
    perm = "platform.telegram.fa.trends.overview"
    # services.check_access(user=current_user, permission=perm)

    return await trends_service.get_trends_overview(start_date, end_date, sort)
