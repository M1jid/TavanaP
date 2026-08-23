from fastapi import APIRouter, Depends, Query, Form, File
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List
from fastapi import UploadFile
from typing import Optional
import logging

from auth.auth import get_current_active_user, User
from services import services
from services.platform.telegram import chats as chats_service

# Logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Telegram Chats"])


@router.get("/admin/active")
async def get_active_admins(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.active"
    services.check_access(user=current_user, permission=perm)

    return await chats_service.get_active_admins()


@router.get("/admin/total-messages-count")
async def get_admin_chats_total_messages_count(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.chats.total.messages.count"
    services.check_access(user=current_user, permission=perm)
    return await chats_service.get_admin_chats_total_messages_count()


@router.get("/admin/total-messages")
async def get_admin_chats_total_messages(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.chats.total.messages"
    services.check_access(user=current_user, permission=perm)
    return await chats_service.get_admin_chats_total_messages()


@router.get("/admin/total-discussions-count")
async def get_admin_chats_total_discussions_count(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.chats.total.discussions.count"
    services.check_access(user=current_user, permission=perm)
    
    return await chats_service.get_admin_chats_total_discussions_count()


@router.get("/admin/scroll")
async def get_admin_chat_messages_scroll(
    reciver: int,
    peer: int,
    size: int,
    page: int,
    reverse: bool,
    current_user: User = Depends(get_current_active_user),
):
    return await chats_service.get_admin_chat_messages_scroll(reciver, peer, size, page, reverse)


@router.get("/admin/peers/scroll")
async def get_admin_chat_peers_scroll(
    size: int = Query(10, description="Number of results to return"),
    admin_filter: Optional[str] = Query(None, description="Admin filter"),
    after_key_peer: Optional[int] = Query(None, description="Pagination cursor"),
    after_key_reciver: Optional[int] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of Telegram chats"""
    perm = "platform.telegram.fa.chats.admin.peers.scroll"
    services.check_access(user=current_user, permission=perm)
    
    return await chats_service.get_admin_chat_peers_scroll(size, admin_filter, after_key_peer, after_key_reciver)


@router.get(
    "/admin/messages",
    summary="Retrieve Chat Messages Between An Admin And A Specific User"
)
async def get_admin_chat_messages(
    reciver: int = Query(..., description="Reciver phone number"),
    peer: int = Query(..., description="Peer ID"),
    size: int = Query(10, description="Number of results to return"),
    page: int = Query(1, description="Page number"),
    reverse: bool = Query(False, description="Reverse order"),
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.messages"
    services.check_access(user=current_user, permission=perm)

    return await chats_service.get_admin_chat_messages(reciver, peer, size, page, reverse)


@router.get(
    "/admin/geographic/report",
    summary="Get Geographic Report of Total Messages"
)
async def get_geographic_report(
    current_user: User = Depends(get_current_active_user),
):
    perm = "platform.telegram.fa.chats.admin.geographic.report"
    services.check_access(user=current_user, permission=perm)

    return await chats_service.get_geographic_report()


@router.post(
    "/admin/send-message",
    summary="Send a message",
)
async def send_message(
    phone_number: int = Form(...),
    user_id: int = Form(...),
    text: str = Form(...),
    reply_to_msg_id: Optional[int] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_active_user),
):
    """Send a message"""
    perm = "platform.telegram.fa.chats.admin.send.message"
    services.check_access(user=current_user, permission=perm)

    # Create a data object to pass to the service
    data = {
        "phone_number": phone_number,
        "user_id": user_id,
        "text": text,
        "reply_to_msg_id": reply_to_msg_id
    }

    return await chats_service.send_message(data, files)