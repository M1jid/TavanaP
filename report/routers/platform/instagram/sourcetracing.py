# from fastapi import APIRouter, Depends, Query
# from datetime import date, timedelta
# from typing import Optional, List
# from pydantic import BaseModel
# from auth.auth import get_current_active_user
# from services.platform.instagram import get_sourcetracing as services

# router = APIRouter(
#     prefix="/timeline",
#     tags=["Instagram Timeline"],
#     dependencies=[Depends(get_current_active_user)],
#     responses={404: {"description": "Not found"}},
# )

# class TimelinePost(BaseModel):
#     username: str
#     caption: str
#     taken_at: Optional[str] = None
#     like_count: int = 0
#     POST_URL: str = ""

# class TimelineResponse(BaseModel):
#     total_posts: int
#     posts: List[TimelinePost] = []

# @router.get(
#     "/instagram_timeline",
#     summary="Get Instagram Posts Timeline",
#     description=(
#         "این endpoint روند انتشار پست‌های اینستاگرام را بر اساس متن جستجو و بازه زمانی مشخص برمی‌گرداند. "
#         "خروجی شامل لیست پست‌ها مرتب‌شده بر اساس زمان انتشار خواهد بود."
#     )
# )
# async def instagram_timeline(
#     search_text: str = Query(..., description="متن موردنظر برای جستجو در کپشن پست‌ها"),
#     start_date: Optional[str] = Query(
#         default=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
#         description="تاریخ شروع بازه تحلیل (YYYY-MM-DD)"
#     ),
#     end_date: Optional[str] = Query(
#         default=date.today().strftime("%Y-%m-%d"),
#         description="تاریخ پایان بازه تحلیل (YYYY-MM-DD)"
#     ),
#     size: int = Query(100, ge=1, description="تعداد نتایج برای نمایش در timeline")
# ):
#     posts = await services(search_text, start_date, end_date, size)
#     return {
#         "total_posts": len(posts),
#         "posts": posts
#     }
