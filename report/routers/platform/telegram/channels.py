from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from typing import Optional, List
from datetime import date, timedelta
from auth.auth import get_current_active_user, User
from schemas import telegram_schemas as schemas
from services import services
from services.platform.telegram import channels as channels_service
from services.platform.telegram.shared_services import TelegramService
from utils import db_handler as db

router = APIRouter(prefix="/channels")


@router.post(
    "/", 
    summary="Create a new Telegram channel", 
    tags=["Telegram Channels"]
)
async def create_channel(
    data: schemas.CreateTelegramChannels,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new Telegram channel"""
    perm = "platform.telegram.fa.channels.create"
    services.check_access(user=current_user, permission=perm)
    
    return await TelegramService.create_channel(data.model_dump())


@router.put(
    "/{id}", 
    summary="Update a Telegram channel", 
    tags=["Telegram Channels"]
)
async def update_channel(
    id: int,
    data: schemas.UpdateTelegramChannels,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new Telegram channel"""
    perm = "platform.telegram.fa.channels.update"
    services.check_access(user=current_user, permission=perm)
    
    return await TelegramService.update_channel(id, data.model_dump())


@router.put(
    "/{id}/block", 
    summary="Block a Telegram channel",
    tags=["Telegram Channels"]
)
async def block_channel(
    id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Block a Telegram channel"""
    perm = "platform.telegram.fa.channels.block"
    services.check_access(user=current_user, permission=perm)
    
    return await TelegramService.block_channel(id)


@router.put(
    "/{id}/unblock", 
    summary="Unblock a Telegram channel",
    tags=["Telegram Channels"]
)
async def unblock_channel(
    id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Unblock a Telegram channel"""
    perm = "platform.telegram.fa.channels.unblock"
    services.check_access(user=current_user, permission=perm)
    
    return await TelegramService.unblock_channel(id)


@router.get(
    "/list", 
    summary="List of Telegram Channels", 
    tags=["Telegram Channels"]
)
async def get_channels_list(
    size: int = Query(10, description="Number of results to return"),
    scroll_id: Optional[str] = Query(None, description="Pagination cursor"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of Telegram channels with optional search and pagination"""
    perm = "platform.telegram.fa.channels.list"
    services.check_access(user=current_user, permission=perm)
    
    return await channels_service.get_channels_list(size, scroll_id, search)


@router.get(
    "/underfollow/all",
    summary="Get Telegram channels under follow",
    tags=["Telegram Channels Underfollow"]
)
async def get_channels_underfollow(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram channels under follow"""
    perm = "platform.telegram.fa.channels.underfollow"
    services.check_access(user=current_user, permission=perm)

    return [{'id': peer_id} for peer_id in current_user.following_channels]


@router.get(
    "/underfollow/status/{channel_id}",
    summary="Get Telegram channels under follow",
    tags=["Telegram Channels Underfollow"]
)
async def get_channels_underfollow_status(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram channels under follow"""
    perm = "platform.telegram.fa.channels.underfollow"
    services.check_access(user=current_user, permission=perm)

    return channel_id in current_user.following_channels


@router.get(
    "/underfollow/details/all",
    summary="Get Telegram channels under follow details",
    tags=["Telegram Channels Underfollow"]
)
async def get_channels_underfollow_details(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram channels under follow"""
    perm = "platform.telegram.fa.channels.underfollow"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_channels_underfollow_details(current_user.following_channels)


@router.delete(
    "/underfollow/{channel_id}",
    summary="Delete Telegram channel under follow",
    tags=["Telegram Channels Underfollow"]
)
async def delete_channel_underfollow(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete Telegram channel under follow"""
    perm = "platform.telegram.fa.channels.underfollow"
    services.check_access(user=current_user, permission=perm)

    if channel_id not in current_user.following_channels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel not under follow")

    current_user.following_channels.remove(channel_id)
    db.update_user(current_user.id, current_user.model_dump())

    return await channels_service.get_channels_underfollow_details(following_channels=[channel_id])


@router.post(
    "/underfollow/{channel_id}",
    summary="Create Telegram channel under follow",
    tags=["Telegram Channels Underfollow"]
)
async def create_channel_underfollow(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Create Telegram channel under follow"""
    perm = "platform.telegram.fa.channels.underfollow"
    services.check_access(user=current_user, permission=perm)

    if channel_id in current_user.following_channels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel already under follow")

    try:
        _ = db.get_telegram_peer(peer_id=channel_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    current_user.following_channels.append(channel_id)
    db.update_user(current_user.id, current_user.model_dump())

    return await channels_service.get_channels_underfollow_details(following_channels=[channel_id])


@router.get(
    "/details/{channel_id}",
    summary="Get Telegram Channel Details",
    tags=["Telegram Channels"]
)
async def get_channel_details(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific Telegram channel"""
    perm = "platform.telegram.fa.channels.details"
    services.check_access(user=current_user, permission=perm)
    
    return await channels_service.get_channel_details(channel_id)


@router.get(
    "/details/overview/{channel_id}",
    summary="Get Telegram Channel Details",
    tags=["Telegram Channels"]
)
async def get_channel_details_overview(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific Telegram channel"""
    perm = "platform.telegram.fa.channels.details"
    services.check_access(user=current_user, permission=perm)
    
    return await channels_service.get_channel_details_overview(channel_id)


@router.get(
    "/overview",
    summary="Get Telegram Channel Overview",
    tags=["Telegram Channels"]
)
async def get_channels_overview_endpoint(
    channel_ids: List[int] = Query(..., description="List of channel IDs to get overview for"),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about multiple Telegram channels"""
    perm = "platform.telegram.fa.channels.details"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_channels_overview(channel_ids)


@router.get(
    "/messages",
    summary="Get Telegram channel messages",
    tags=["Telegram Channels"]
)
async def get_channel_messages(
    size: int = Query(default=12, example=12, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    selected_channels: List[int] = Query(default=[], example=[], description="List of channel IDs to get messages for"),
    start_date: str = Query(default=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    search_text: str = Query("", description="Search text"),
    sentiment: str = Query(default="", example="", description="Sentiment: خنثی, مثبت, منفی"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram channel messages based on filters"""
    perm = "platform.telegram.fa.channels.messages"
    services.check_access(user=current_user, permission=perm)
    
    if not search_text:
        search_text = ''
    if not start_date:
        start_date = default=(date.today() - timedelta(days=365*10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    return await channels_service.get_channel_messages(size, page, selected_channels, start_date, end_date, search_text, sentiment)


@router.get(
    "/comments",
    summary="Get Telegram channel comments",
    tags=["Telegram Channels"]
)
async def get_channel_comments(
    size: int = Query(default=12, example=12, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    selected_channels: List[int] = Query(default=[], example=[], description="List of channel IDs to get messages for"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    search_text: str = Query("", description="Search text"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram channel comments based on filters"""
    perm = "platform.telegram.fa.channels.comment"
    services.check_access(user=current_user, permission=perm)
    
    if not search_text:
        search_text = ''
    if not start_date:
        start_date = default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    return await channels_service.get_channel_comments(size, page, selected_channels, start_date, end_date, search_text)


@router.get(
    "/message/details",
    summary="Get Telegram message details",
    tags=["Telegram Channels"]
)
async def get_message_details(
    peer_id: int = Query(..., description="Message Peer ID"),
    message_id: int = Query(..., description="Message ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram message details"""
    perm = "platform.telegram.fa.channels.message.details"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_message_details(f'https://t.me/c/{peer_id}/{message_id}')


@router.post(
    "/upload-image/{channel_id}",
    summary="Upload Channel Image",
    description="Upload a profile image for a specific Telegram channel",
    tags=["Telegram Channels"]
)
async def upload_channel_image(
    channel_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a profile image for a specific Telegram channel"""
    perm = "platform.telegram.fa.channels.upload.image"
    services.check_access(user=current_user, permission=perm)

    return await TelegramService.upload_channel_image(channel_id, file)


@router.get(
    "/owned-channels",
    summary="Get Telegram owned channels",
    tags=["Telegram Channels"]
)
async def get_owned_channels(
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram owned channels"""
    perm = "platform.telegram.fa.channels.owned"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_owned_channels()


@router.get(
    "/owned-channels/report",
    summary="Get Telegram owned channels report",
    tags=["Telegram Channels"]
)
async def get_owned_channels_report(
    channel_id: int = Query(..., description="Channel ID"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=12, example=12, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram owned channels report"""
    perm = "platform.telegram.fa.channels.owned"
    services.check_access(user=current_user, permission=perm)
    
    if not start_date:
        start_date = default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    return await channels_service.get_owned_channels_report(channel_id=channel_id, start_date=start_date, end_date=end_date, size=size, page=page)


@router.get(
    "/sourcetracing",
    tags=["Telegram Channels"]
)
async def get_sourcetracing(
    search_text: str = Query(default="تورم", example="تورم", description="message to search"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=100, example=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user)
) -> list[dict]:
    perm = "platform.telegram.fa.posts.sourcetracing"
    services.check_access(user=current_user, permission=perm)
    
    if not search_text:
        search_text = ''
    if not start_date:
        start_date = default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")
    
    return await channels_service.get_sourcetracing(search_text, start_date, end_date, size)


@router.get(
    "/insights",
    tags=["Telegram Channels"]
)
async def get_insights(
    search_text: str = Query(default="تورم", example="تورم", description="message to search"),
    size: int = Query(default=100, example=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.posts.sourcetracing"
    services.check_access(user=current_user, permission=perm)
    
    return await channels_service.get_insights(search_text, size)


@router.get(
    "/similar-channels",
    tags=["Telegram Channels"]
)
async def get_similar_channels(
    search_text: str = Query(default="تورم", example="تورم", description="message to search"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=100, example=100, description="Number of results to return"),
    sort: str = Query(default="VIEWS", example="VIEWS", description="Sort by 'DATE' or 'VIEWS'"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.channels.similar"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_similar_channels(search_text, start_date, end_date, size, sort)


@router.get(
    "/forwarding",
    summary="Get Telegram forwarding info",
    tags=["Telegram Channels"]
)
async def get_forwarding_info():
    """
    Returns the top forwarded channels and their forwarding channels.
    Data is fetched from Elasticsearch aggregation directly.
    """
    return await channels_service.parse_forwarding_aggregation()


@router.get(
    "/keyword-top-channels",
    tags=["Telegram Channels"]
)
async def get_keyword_top_channels(
    search_text: str = Query(default="null", example="تورم", description="Message to search. Use 'null' to use subject filters"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    subject_type: str = Query(default="null", example="topic", description="Type of the subject: 'topic', 'person', 'event' or 'force'"),
    subject_id: int = Query(default=0, example=0, description="Unique ID of the subject"),
    size: int = Query(default=10, example=10, description="Number of top channels to return"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.channels.keyword.top.channels"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_keyword_top_channels(search_text, start_date, end_date, subject_type, subject_id, size)


@router.get(
    "/content/report-tags",
    summary="Get Telegram content report with tags",
    tags=["Telegram Channels"]
)
async def get_content_report(
    search_text: str = Query(default="تورم", example="تورم", description="Search term"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=10, example=10, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    sort: str = Query(default="VIEWS", example="VIEWS", description="Sort by 'DATE', 'FORWARDS', 'VIEWS', 'REACTIONS' or 'COMMENTS'"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.channels.content.report.tags"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_content_report(search_text, start_date, end_date, size, page, sort)


@router.get(
    "/content/report-no-tags",
    summary="Get Telegram content report without tags",
    tags=["Telegram Channels"]
)
async def get_content_report_no_tags(
    search_text: str = Query(default="تورم", example="تورم", description="Search term"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=10, example=10, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    sort: str = Query(default="VIEWS", example="VIEWS", description="Sort by 'DATE', 'FORWARDS', 'VIEWS', 'REACTIONS' or 'COMMENTS'"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.channels.content.report.no.tags"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_content_report_no_tags(search_text, start_date, end_date, size, page, sort)


@router.get(
    "/geographic/report",
    summary="Get Telegram geographic report",
    description="Returns the number of times each city name appears in Telegram messages (post) and in the message URL (url).",
    tags=["Telegram Channels"]
)
async def get_geographic_report(
    search_text: str = Query(default="null", example="null", description="Search term (use 'null' to disable it)"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    subject_type: str = Query(default="null", example="null", description="Type of the subject: 'topic', 'person', 'event' or 'force' (use when search term is 'null')"),
    subject_id: int = Query(default=0, example=0, description="Unique ID of the subject (use when search term is 'null')"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.geographic.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_geographic_report(search_text, start_date, end_date, subject_type, subject_id)    


@router.get(
    "/aja-channels-analysis",
    summary="Get analysis for Aja Telegram channels",
    tags=["Telegram Channels"]
)
async def get_aja_channels_analysis(
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.aja.channels.analysis.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_aja_channels_analysis(start_date, end_date)


@router.get(
    "/aja-channels-subs",
    summary="Get analysis for subscribers of Aja Telegram channels",
    tags=["Telegram Channels"]
)
async def get_aja_channels_subs(
    num_recent_months: int = Query(default=6, example=6, description="Number of recent months to include in the analysis"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.aja.channels.subs.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_aja_channels_subs(num_recent_months)


@router.post(
    "/add-new-aja-channel",
    summary="Add a new Aja channel",
    tags=["Telegram Channels"]
)
async def add_new_aja_channel(
    url: str = Query(..., description="Channel URL"),
    tag: str = Query(..., description="Channel tag"),
    admin: str = Query(..., description="Channel admin name"),
    city: str = Query(..., description="City of the channel"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.add.new.aja.channel.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.add_new_aja_channel(url, tag, admin, city)


@router.delete(
    "/delete-aja-channel",
    summary="Delete an Aja channel",
    tags=["Telegram Channels"]
)
async def delete_aja_channel(
    url: str = Query(..., description="Channel URL to delete"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.delete.aja.channel.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.delete_aja_channel(url)


@router.get(
    "/aja-channels-admins",
    summary="Get Aja channels admins",
    tags=["Telegram Channels"]
)
async def aja_channels_admins(
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.aja.channels.admins.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_aja_channels_admins()


@router.post(
    "/add-new-admin-aja-channels",
    summary="Add a new admin in an Aja channel",
    tags=["Telegram Channels"]
)
async def add_new_admin_aja_channels(
    channel_url: str = Query(..., description="Channel URL"),
    name: str = Query(..., description="Admin name"),
    national_id: str = Query(..., description="Admin national ID"),
    phone: str = Query(..., description="Admin phone number"),
    account_email: str = Query(..., description="Admin account email"),
    account_phone: str = Query(..., description="Admin account phone"),
    address: str = Query(..., description="Admin address"),
    isCreator: int = Query(..., description="Is creator"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.add.new.admin.aja.channels.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.add_new_admin_aja_channels(channel_url, name, national_id, phone, account_email, account_phone, address, isCreator)


@router.delete(
    "/delete-admin-aja-channels",
    summary="Delete an admin in an Aja channel",
    tags=["Telegram Channels"]
)
async def delete_an_admin_aja_channels(
    channel_url: str = Query(..., description="Channel URL"),
    admin_id: str = Query(..., description="Admin ID"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.delete.admin.aja.channels.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.delete_an_admin_aja_channels(channel_url, admin_id)


@router.get(
    "/c2-system-analysis",
    summary="Get analysis for C2 System",
    tags=["Telegram Channels"]
)
async def get_c2_system_analysis(
    start_date: str = Query(default=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.c2.system.analysis.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_c2_system_analysis(start_date, end_date)


@router.get(
    "/c2-system-messages",
    summary="Get messages of the Aja channels for C2 System",
    tags=["Telegram Channels"]
)
async def get_c2_system_messages(
    start_date: str = Query(default=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=10, example=10, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.c2.system.messages.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_c2_system_messages(start_date, end_date, size, page)


@router.get(
    "/c2-system-geographic",
    summary="Get geographic report for C2 System",
    description="Returns the total number of occurence of each city in the Aja channels by 'city' field. Also, return the number of forces tag for each city.",
    tags=["Telegram Channels"]
)
async def get_c2_system_geographic(
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.c2.system.geographic.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_c2_system_geographic()


@router.get(
    "/c2-system-subscribers-growth",
    summary="Get subscribers growth rate report for Aja telegram channels",
    tags=["Telegram Channels"]
)
async def get_c2_system_subscribers_growth(
    start_date: str = Query(default=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.c2.system.subscribers.growth"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_c2_system_subscribers_growth(start_date, end_date)


@router.get(
    "/query-aggs",
    summary="Get Telegram query aggs info",
    tags=["Telegram Queries (Topic-Person-Event-Force)"]
)
async def get_query_by_aggs(
    subject_type: str = Query(default="topic", example="topic", description="Subject of The Query (topic, person, event, force)"),
    search_id: int = Query(default=1, example=1, description="Search ID of The Subject"),
    message_type: str = Query(default="CHANNELPOST", example="CHANNELPOST", description="Messages type 'CHANNELPOST' or 'CHANNELCOMMENT'"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.query.by.aggs.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_query_by_aggs(subject_type, search_id, message_type, start_date, end_date)


@router.get(
    "/query-msg",
    summary="Get Telegram query messages info",
    tags=["Telegram Queries (Topic-Person-Event-Force)"]
)
async def get_query_by_msg(
    subject_type: str = Query(default="topic", example="topic", description="Subject of The Query (topic, person, event, force)"),
    search_id: int = Query(default=1, example=1, description="Search ID of The Subject"),
    message_type: str = Query(default="CHANNELPOST", example="CHANNELPOST", description="Messages type 'CHANNELPOST' or 'CHANNELCOMMENT'"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    size: int = Query(default=10, example=10, description="Number of results to return"),
    page: int = Query(default=1, example=1, description="Pagination cursor"),
    sort: str = Query(default="DATE", example="DATE", description="Sort by 'DATE' or 'VIEWS'"),
    current_user: User = Depends(get_current_active_user)
):
    perm = "platform.telegram.fa.query.by.msg.report"
    services.check_access(user=current_user, permission=perm)

    return await channels_service.get_query_by_msg(subject_type, search_id, message_type, start_date, end_date, size, page, sort)
