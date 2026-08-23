from fastapi import APIRouter, Depends, Query
from services import services
from services.platform.telegram import daily_report as daily_report_services
from auth.auth import get_current_active_user, User


router = APIRouter(prefix="/daily", tags=["Telegram Daily Report"])


@router.get(
    "/popular-posts",
    summary="Get Telegram's daily popular posts"
)
async def get_popular_posts(
    current_user: User = Depends(get_current_active_user)
):
    """
    Return the top 20 Telegram posts from the past day,
    sorted by views.
    """
    perm = "platform.telegram.fa.daily.popular.posts"
    services.check_access(user=current_user, permission=perm)

    return await daily_report_services.get_popular_posts()


@router.get(
    "/popular-channels",
    summary="Get Telegram's daily popular channels"
)
async def get_popular_channels(
    current_user: User = Depends(get_current_active_user)
):
    """
    Return the top 20 Telegram channels from the past day,
    sorted by views.
    """
    perm = "platform.telegram.fa.daily.popular.channels"
    services.check_access(user=current_user, permission=perm)

    return await daily_report_services.get_popular_channels()


@router.get(
    "/similar-messages",
    summary="Get Telegram's daily similar messages"
)
async def get_similar_messages(
    similarity_threshold: int = Query(default=30, example=30, description="Minimum score of similarity"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Return the top 5 Telegram messages per top 5 tags that are similar to each tag's top message from the past day.
    Only messages with a similarity score above the specified threshold are included.
    """
    perm = "platform.telegram.fa.daily.similar.messages"
    services.check_access(user=current_user, permission=perm)

    return await daily_report_services.get_similar_messages(similarity_threshold)


# @router.get(
#     "/trending-news-summary",
#     summary="Get Telegram's daily trending news summary"
# )
# async def get_trending_news_summary(
#     current_user: User = Depends(get_current_active_user)
# ):
#     perm = "platform.telegram.fa.daily.trending.news.summary"
#     services.check_access(user=current_user, permission=perm)

#     return await daily_report_services.get_trending_news_summary()


# @router.get("/wordcloud",
#     summary="Get Telegram's daily wordcloud"
# )
# async def get_wordcloud(
#     current_user: User = Depends(get_current_active_user)
# ):
#     perm = "platform.telegram.fa.daily.wordcloud"
#     services.check_access(user=current_user, permission=perm)

#     return await daily_report_services.get_wordcloud()


@router.get(
    "/most-reaction-channels",
    summary="Get Telegram's daily most reaction channels"
)
async def get_most_reaction_channels(
    current_user: User = Depends(get_current_active_user)
):
    """
    Return the top Telegram channels from the past day,
    sorted by number of total reactions.
    """
    perm = "platform.telegram.fa.daily.most.reaction.channels"
    services.check_access(user=current_user, permission=perm)

    return await daily_report_services.get_most_reaction_channels()


@router.get("/most-comment-channels",
    summary="Get Telegram's daily most comment channels"
)
async def get_most_comment_channels(
    current_user: User = Depends(get_current_active_user)
):
    """
    Return the top Telegram channels from the past day,
    sorted by number of total comments.
    """
    perm = "platform.telegram.fa.daily.most.comment.channels"
    services.check_access(user=current_user, permission=perm)

    return await daily_report_services.get_most_comment_channels()
