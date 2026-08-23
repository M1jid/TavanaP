from fastapi import APIRouter, Depends, HTTPException

from auth.auth import get_current_active_user

from routers.platform.instagram.trends import router as trends_router
from routers.platform.instagram.pages import router as pages_router
from routers.platform.instagram.filters import router as filter_router
# from routers.instagram.timeline import router as timeline_router  
router = APIRouter(
    prefix="/fa/instagram",
    # dependencies=[Depends(get_current_active_user)],
)

router.include_router(trends_router)
router.include_router(pages_router)
router.include_router(filter_router)
# router.include_router(timeline_router)  
