from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from pydantic import BaseModel

from datetime import date, timedelta

from auth.auth import get_current_active_user, User

from services.platform.telegram import posts as posts_service
from services import services


router = APIRouter(prefix="/posts", tags=["Telegram Posts"])


class PeerCompletionRequest(BaseModel):
    job_id: str
    peer_id: int
    status: str  # "completed" or "failed"
    error_message: str = None

@router.put("/")
async def create_update_job(
    search_text: str = Query(default="تورم", example="تورم", description="message to search"),
    start_date: str = Query(default=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), example=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d"), description="Start date of the analysis range"),
    end_date: str = Query(default=date.today().strftime("%Y-%m-%d"), example=date.today().strftime("%Y-%m-%d"), description="End date of the analysis range"),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new message update job and return job ID immediately"""
    perm = "platform.telegram.fa.update.posts"
    services.check_access(user=current_user, permission=perm)

    if not search_text:
        search_text = ''
    if not start_date:
        start_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")
    
    return await posts_service.create_update_job(search_text, start_date, end_date)

@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get the status of an update job"""
    perm = "platform.telegram.fa.update.posts"
    services.check_access(user=current_user, permission=perm)
    
    return await posts_service.get_job_status(job_id)


@router.post("/peer-completion")
async def report_peer_completion(
    request: PeerCompletionRequest,
    # current_user: User = Depends(get_current_active_user),
):
    """Report completion of a peer update (fallback endpoint for Telegram clients)"""
    perm = "platform.telegram.fa.update.posts"
    # services.check_access(user=current_user, permission=perm)
    
    if request.status not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Status must be 'completed' or 'failed'")
    
    await posts_service.mark_peer_completed(
        request.job_id, 
        request.peer_id, 
        request.status, 
        request.error_message
    )
    
    return {"message": f"Peer {request.peer_id} marked as {request.status}"}
