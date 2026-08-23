from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, timedelta
import asyncio
from auth.auth import get_current_active_user
# from schemas.instagram import trends as schemas
from services.platform.instagram import trends as services

router = APIRouter(
    prefix="/trends",
    tags=["Instagram Trends"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/overview",
    summary="Get Top Instagram Trends Overview",
    description=(
        "این endpoint نمای کلی از ترندهای برتر اینستاگرام را در بازه زمانی مشخص شده ارائه می‌دهد. "
        "خروجی شامل آمار کلی ترندها، صفحات برتر، تعداد پست‌ها، میزان تعاملات و سایر شاخص‌های تحلیلی است."
    ),
)
async def get_trends_overview(
    start_date: str = Query(
        default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="تاریخ شروع بازه تحلیل (YYYY-MM-DD)"
    ),
    end_date: str = Query(
        default=date.today().strftime("%Y-%m-%d"),
        example=date.today().strftime("%Y-%m-%d"),
        description="تاریخ پایان بازه تحلیل (YYYY-MM-DD)"
    ),
    # current_user: User = Depends(get_current_active_user),
):
    """
    دریافت نمای کلی ترندهای برتر اینستاگرام در بازه زمانی مشخص.

    پارامترها:
    - start_date: تاریخ شروع تحلیل
    - end_date: تاریخ پایان تحلیل

    خروجی:
    - دیکشنری شامل ترندهای برتر، صفحات برتر، تعداد پست‌ها و سایر شاخص‌های آماری.
    """
    return await services.instagram_top_trend(
        start_date=start_date,
        end_date=end_date
    )
