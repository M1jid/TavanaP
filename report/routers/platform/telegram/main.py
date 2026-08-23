from fastapi import APIRouter, Depends, HTTPException

from auth.auth import get_current_active_user

from routers.platform.telegram.channels import router as channels_router
from routers.platform.telegram.groups import router as groups_router
from routers.platform.telegram.trends import router as trends_router
from routers.platform.telegram.wordcloud import router as wordcloud_router
from routers.platform.telegram.users import router as users_router
from routers.platform.telegram.daily_report import router as daily_report_router
from routers.platform.telegram.posts import router as posts_router
from routers.platform.telegram.chats import router as chats_router
from routers.platform.telegram.accounts import router as accounts_router

router = APIRouter(
    prefix="/fa/telegram",
    # dependencies=[Depends(get_current_active_user)],
)

router.include_router(channels_router)
router.include_router(groups_router)
router.include_router(trends_router)
router.include_router(wordcloud_router)
router.include_router(users_router)
router.include_router(daily_report_router)
router.include_router(posts_router)
router.include_router(chats_router)
router.include_router(accounts_router)