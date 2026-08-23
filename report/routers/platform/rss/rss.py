from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta
from services import services
from services.platform.rss import rss as rss_service
from auth.auth import get_current_active_user, User

router = APIRouter(prefix="/rss",)


@router.get(
    "/aja-website-analysis",
    summary="Get RSS analysis for the Aja website",
    description=(
        "Retrieves and analyzes RSS feed data from the official Aja website "
        "(`aja.ir`) for a given date range."
    ),
    status_code=200,
    tags=["RSS"]
)
async def get_aja_website_analysis(
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.rss.fa.aja.website.analysis.report"
    services.check_access(user=current_user, permission=perm)

    return await rss_service.get_aja_website_analysis(start_date, end_date)


@router.get(
    "/query-aggs",
    summary="Get RSS query aggs info",
    description=(
        "Retrieves aggregated RSS analytics for a given subject type (topic, person, event, or force) and search ID "
        "within a date range. Returns total document count, sentiment distribution, publisher breakdown, hourly activity, "
        "and historical trends."
    ),
    status_code=200,
    tags=["RSS Queries (Topic-Person-Event-Force)"]
)
async def get_query_by_aggs(
    subject_type: str = Query(default="topic", example="topic", description="Subject of the query (topic, person, event, force)"),
    search_id: int = Query(default=1, example=1, description="Search ID of the subject"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.rss.fa.query.by.aggs.report"
    services.check_access(user=current_user, permission=perm)

    return await rss_service.get_query_by_aggs(subject_type, search_id, start_date, end_date)


@router.get(
    "/query-msg",
    summary="Get RSS query messages info",
    description=(
        "Fetches RSS messages related to a specific subject type (topic, person, event, or force) and search ID "
        "within a given date range. Returns a paginated list of messages with details such as title, summary, author, "
        "channel, sentiment, and tags."
    ),
    status_code=200,
    tags=["RSS Queries (Topic-Person-Event-Force)"]
)
async def get_query_by_msg(
    subject_type: str = Query(default="topic", example="topic", description="Subject of the query (topic, person, event, force)"),
    search_id: int = Query(default=1, example=1, description="Search ID of the subject"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=10, example=10, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.rss.fa.query.by.msg.report"
    services.check_access(user=current_user, permission=perm)

    return await rss_service.get_query_by_msg(subject_type, search_id, start_date, end_date, size, page)