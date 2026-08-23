from fastapi import APIRouter, Depends, HTTPException

from auth.auth import get_current_active_user
from routers.platform.telegram import main as telegram_router
from routers.platform.twitter import twitter
from routers.platform.instagram import main as instagram_router
from routers.platform.rss import rss
from routers.platform.action_users.admin import users as admin_user
from routers.platform.action_users.admin import queries as admin_queries
from routers.platform.action_users.user import users as regular_user
from routers.platform.action_users.user import queries as regular_queries
from routers.platform import default


router = APIRouter(
    prefix="/platform",
    # dependencies=[Depends(get_current_active_user)],
)


# Include other platform routers
router.include_router(telegram_router.router)
router.include_router(instagram_router.router)

router.include_router(twitter.router)
router.include_router(rss.router)
router.include_router(default.router)

router.include_router(admin_user.router)
router.include_router(admin_queries.router)

router.include_router(regular_user.router)
router.include_router(regular_queries.router)

