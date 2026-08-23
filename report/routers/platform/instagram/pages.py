from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta
from typing import Optional
from auth.auth import get_current_active_user
from services.platform.instagram import pages as services

router = APIRouter(
    prefix="/trends",
    tags=["Instagram Trends"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/aja-pages-analysis",
    summary="Get Analysis of Instagram Pages of Aja",
    description=(
        "این endpoint تحلیل صفحات اینستاگرام Aja را در بازه مشخص شده برمی‌گرداند. "
        "خروجی شامل اطلاعات آماری، روندها و احتمالا aggregations مربوط به صفحات خواهد بود."
    )
)
async def get_aja_pages_analysis(
    start_date: Optional[str] = Query(
        default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
        description="تاریخ شروع بازه تحلیل (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(
        default=date.today().strftime("%Y-%m-%d"),
        example=date.today().strftime("%Y-%m-%d"),
        description="تاریخ پایان بازه تحلیل (YYYY-MM-DD)"
    ),
):
    """
    دریافت تحلیل صفحات اینستاگرام Aja در بازه مشخص.

    پارامترها:
    - start_date: تاریخ شروع تحلیل
    - end_date: تاریخ پایان تحلیل

    خروجی:
    - دیکشنری شامل آمار صفحات اینستاگرام، روندها و اطلاعات تحلیلی.
    """
    return await services.get_aja_pages_analysis(
        start_date=start_date,
        end_date=end_date
    )
