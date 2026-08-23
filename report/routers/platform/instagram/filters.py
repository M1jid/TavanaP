# router_instagram.py
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from auth.auth import get_current_active_user
from services.platform.instagram import posts_by_filters as instagram_service


router = APIRouter(
    prefix="/Filter",
    tags=["Instagram Posts Filters"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

VALID_SORTS = ["LIKES", "COMMENTS", "DATE", "VIEWS"]

# ----------------- Pydantic Models -----------------
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class CommentItem(BaseModel):
    username: str
    text: str
    time: Optional[str] = None
    like_count: int = 0
    replies_count: int = 0

class PostItem(BaseModel):
    username: str
    caption: str
    DATE: Optional[str] = None
    day: Optional[str] = None
    hour: Optional[str] = None
    like_count: int = 0
    comments_count: int = 0
    views_count: int = 0  # قبلاً VIEWS_COUNT
    SENTIMENT: Optional[str] = None
    TAGS: Union[List[str], str] = []
    SENSE: List[str] = []
    post_id: Optional[str] = None
    # shortcode: Optional[str] = None
    url: str = ""
    img: str = "" 
    # comments: List[CommentItem] = []  # اضافه کردن لیست کامنت‌ها
    hashtags: List[str] = []
    mentions: List[str] = []
    location: Optional[str] = None
    owner_profile_pic: Optional[str] = None

class Stats(BaseModel):
    likes: int = 0
    comments: int = 0
    forwards: int = 0
    views: int = 0

class InstagramQueryResponse(BaseModel):
    doc_count: int
    history: List[Dict[str, Any]] = []
    sentimentBreakdown: Dict[str, int] = {}
    senseBreakdown: Dict[str, int] = {}
    hoursBreakdown: Dict[str, int] = {}
    hashtagsBreakdown: Dict[str, int] = {}
    mentionsBreakdown: Dict[str, int] = {}
    locationsBreakdown: Dict[str, int] = {}
    stats: Stats = Stats()
    publishers: int = 0
    top_posts: List[PostItem] = []
    # raw_hits: Optional[List[Dict[str, Any]]] = []
    # aggregations: Optional[Dict[str, Any]] = {}
# ----------------- Helper Function -----------------
async def get_query(
    service_func,
    search_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    size: int = 10,
    page: int = 1,
    sort: str = "LIKES"
):
    if sort not in VALID_SORTS:
        raise HTTPException(status_code=400, detail=f"Invalid sort value: {sort}")
    return await service_func(search_id, start_date, end_date, size, page, sort)

# ----------------- Endpoints -----------------
def default_start_date():
    return (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")

def default_end_date():
    return date.today().strftime("%Y-%m-%d")

@router.get(
    "/topic",
    response_model=InstagramQueryResponse,
    summary="Retrieve Instagram posts filtered by topic",
    description="این endpoint پست‌های اینستاگرام را بر اساس یک موضوع مشخص فیلتر می‌کند و اطلاعات کامل پست‌ها و آمار aggregations را برمی‌گرداند."
)
async def insta_query_by_topic(
    search_id: int = Query(1, ge=1, description="شناسه موضوع که می‌خواهید پست‌های آن را دریافت کنید"),
    start_date: str = Query(default_factory=default_start_date, description="تاریخ شروع (YYYY-MM-DD)"),
    end_date: str = Query(default_factory=default_end_date, description="تاریخ پایان (YYYY-MM-DD)"),
    size: int = Query(10, ge=1, description="تعداد نتایج در هر صفحه"),
    page: int = Query(1, ge=1, description="شماره صفحه برای pagination"),
    sort: str = Query("LIKES", description="مرتب‌سازی بر اساس: LIKES, COMMENTS, DATE, VIEWS")
):
    return await get_query(instagram_service.get_instagram_query_by_topic, search_id, start_date, end_date, size, page, sort)

@router.get(
    "/person",
    response_model=InstagramQueryResponse,
    summary="Retrieve Instagram posts filtered by person",
    description="این endpoint پست‌های اینستاگرام را بر اساس یک شخص مشخص فیلتر می‌کند و اطلاعات کامل پست‌ها و آمار aggregations را برمی‌گرداند."
)
async def insta_query_by_person(
    search_id: int = Query(1, ge=1, description="شناسه شخص که می‌خواهید پست‌های آن را دریافت کنید"),
    start_date: str = Query(default_factory=default_start_date, description="تاریخ شروع (YYYY-MM-DD)"),
    end_date: str = Query(default_factory=default_end_date, description="تاریخ پایان (YYYY-MM-DD)"),
    size: int = Query(10, ge=1, description="تعداد نتایج در هر صفحه"),
    page: int = Query(1, ge=1, description="شماره صفحه برای pagination"),
    sort: str = Query("LIKES", description="مرتب‌سازی بر اساس: LIKES, COMMENTS, DATE, VIEWS")
):
    return await get_query(instagram_service.get_insta_query_by_person, search_id, start_date, end_date, size, page, sort)

@router.get(
    "/event",
    response_model=InstagramQueryResponse,
    summary="Retrieve Instagram posts filtered by event",
    description="این endpoint پست‌های اینستاگرام را بر اساس یک رویداد مشخص فیلتر می‌کند و اطلاعات کامل پست‌ها و آمار aggregations را برمی‌گرداند."
)
async def insta_query_by_event(
    search_id: int = Query(1, ge=1, description="شناسه رویداد که می‌خواهید پست‌های آن را دریافت کنید"),
    start_date: str = Query(default_factory=default_start_date, description="تاریخ شروع (YYYY-MM-DD)"),
    end_date: str = Query(default_factory=default_end_date, description="تاریخ پایان (YYYY-MM-DD)"),
    size: int = Query(10, ge=1, description="تعداد نتایج در هر صفحه"),
    page: int = Query(1, ge=1, description="شماره صفحه برای pagination"),
    sort: str = Query("LIKES", description="مرتب‌سازی بر اساس: LIKES, COMMENTS, DATE, VIEWS")
):
    return await get_query(instagram_service.get_insta_query_by_event, search_id, start_date, end_date, size, page, sort)

@router.get(
    "/force",
    response_model=InstagramQueryResponse,
    summary="Retrieve Instagram posts filtered by force",
    description="این endpoint پست‌های اینستاگرام را بر اساس یک نیروی مشخص (Force) فیلتر می‌کند و اطلاعات کامل پست‌ها و آمار aggregations را برمی‌گرداند."
)
async def insta_query_by_force(
    search_id: int = Query(1, ge=1, description="شناسه نیرویی که می‌خواهید پست‌های آن را دریافت کنید"),
    start_date: str = Query(default_factory=default_start_date, description="تاریخ شروع (YYYY-MM-DD)"),
    end_date: str = Query(default_factory=default_end_date, description="تاریخ پایان (YYYY-MM-DD)"),
    size: int = Query(10, ge=1, description="تعداد نتایج در هر صفحه"),
    page: int = Query(1, ge=1, description="شماره صفحه برای pagination"),
    sort: str = Query("LIKES", description="مرتب‌سازی بر اساس: LIKES, COMMENTS, DATE, VIEWS")
):
    return await get_query(instagram_service.get_insta_query_by_force, search_id, start_date, end_date, size, page, sort)
