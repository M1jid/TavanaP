from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from typing import Optional
from auth.auth import get_current_active_user, User
from services import services
from services.platform.telegram.shared_services import TelegramService
from utils import db_handler as db

router = APIRouter(prefix="/admin_user/queries", tags=["Actions Admin"])
import logging
logger = logging.getLogger(__name__)


@router.get(
    "",
    summary="Get all user queries"
)
async def get_user_queries_all(
    query_id: Optional[int] = Query(None, description="Query ID"),
    user_id: Optional[int] = Query(None, description="User ID"),
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    if query_id and user_id:
        raise HTTPException(status_code=400, detail="You cannot get a query by both query_id and user_id")
    if query_id:
        return db.get_user_query_id(query_id)
    if user_id:
        user = db.get_user_by_id(user_id)
        result = []
        for query_id in user['query_ids']:
            query = db.get_user_query_id(query_id)
            result.append(query)
        return result
    return db.get_user_query_id_all()

@router.post(
    "/{user_id}",
    summary="Add a new topic, event or person query"
)
async def add_query(
    user_id: int,
    title: str = Query(default=" ", example=" ", description="Title of query to add"),
    description: str = Query(default="", example="", description="Description of query to add"),
    must: list = Query(default=[], example=[], description="MUST words of query"),
    should: list = Query(default=[], example=[], description="SHOULD words of query"),
    must_not: list = Query(default=[], example=[], description="MUST_NOT words of query"),
    img: UploadFile = File(...),
    type: int = Query(default=1, example=1, description="1 is Topic, 2 is Person, 3 is Event"),
    current_user: User = Depends(get_current_active_user),
):
    """ Add the new query for each user """
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    user = db.get_user_by_id(user_id)
    logger.info(user)
    query = db.create_user_query_id(
        data=[{
            "title": title,
            "description": description,
            "must": must,
            "should": should,
            "must_not": must_not,
            "query_type": type,
        }]
    )
    
    logger.info(query[0]['id'])
    user['query_ids'].append(query[0]['id'])
    logger.info(user)
    db.update_user(user_id, user)
    return await TelegramService.upload_query_image(query[0]['id'], img)

@router.put(
    "/{query_id}",
    summary="Update a topic, event or person query"
)
async def update_query(
    query_id: int,
    title: str = Query(default=" ", example=" ", description="Title of query to add"),
    description: str = Query(default="", example="", description="Description of query to add"),
    must: list = Query(default=[], example=[], description="MUST words of query"),
    should: list = Query(default=[], example=[], description="SHOULD words of query"),
    must_not: list = Query(default=[], example=[], description="MUST_NOT words of query"),
    # img: Optional[UploadFile] = File(None),
    type: int = Query(default=1, example=1, description="1 is Topic, 2 is Person, 3 is Event"),
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    
    new_q = db.update_user_query_id(query_id, data=[{
        "title": title,
        "description": description,
        "must": must,
        "should": should,
        "must_not": must_not,
        "query_type": type,
    }])
    # if img:
    #     await TelegramService.upload_query_image(query_id, img)
    return new_q

@router.delete(
    "/{query_id}",
    summary="Delete a query"
)
async def delete_query(
    query_id: int,
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    return db.delete_user_query_id(query_id)
