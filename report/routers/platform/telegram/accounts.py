from fastapi import APIRouter, Depends, Query
from typing import Optional
import logging

from auth.auth import get_current_active_user, User
from services import services
from utils import db_handler as db
from services.platform.telegram import accounts as accounts_service

# Logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["Telegram Accounts"])


@router.get("/")
async def get_accounts_list(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.accounts.list"
    services.check_access(user=current_user, permission=perm)

    return db.get_telegram_accounts()

@router.post("/send_code")
async def send_code(phone: str):
    return accounts_service.send_code(phone)

@router.post("/verify_code")
async def verify_code(phone: str, code: str):
    return accounts_service.verify_code(phone, code)

@router.post("/verify_password")
async def verify_password(phone: str, password: str):
    return accounts_service.verify_password(phone, password)
