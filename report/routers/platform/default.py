import jdatetime

from fastapi import APIRouter, Depends, Query
from datetime import date
from services import services
from services.platform import default as default_service
from auth.auth import get_current_active_user, User

router = APIRouter(prefix="/default",)


@router.get(
    "/daily-received-messages",
    summary="Get the total number of daily received messages",
    tags=["Default"]
)
async def get_daily_received_messages(
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.default.fa.daily.received.messages.report"
    services.check_access(user=current_user, permission=perm)

    return await default_service.get_daily_received_messages()