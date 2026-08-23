from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from typing import Optional
from auth.auth import get_current_active_user, User
from services import services
from services import user as user_service
from services.platform.telegram.shared_services import TelegramService
from utils import db_handler as db

router = APIRouter(prefix="/user/queries/me", tags=["Actions User"])
import logging
logger = logging.getLogger(__name__)


@router.get(
    "",
    summary="Get all user queries"
)
async def get_user_queries(
    current_user: User = Depends(get_current_active_user),
):
    result = []
    for query_id in current_user.query_ids:
        query = db.get_user_query_id(query_id)
        result.append(query)
    return result

@router.post(
    "",
    summary="Add a new topic, event or person query"
)
async def add_query_me(
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
    logger.info(f"Query: {query}")
    current_user.query_ids.append(query[0]['id'])
    logger.info(current_user)
    logger.info(current_user.model_dump(exclude={'id'}))
    db.update_user(current_user.id, current_user.model_dump(exclude={'id'}))
    return await TelegramService.upload_query_image(query[0]['id'], img)

@router.put(
    "/upload-image/{query_id}",
    summary="Upload query image",
    description="Upload a profile image for a specific Telegram query"
)
async def upload_query_image(
    query_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a profile image for a specific Telegram query"""

    return await TelegramService.upload_query_image(query_id, file)

@router.put(
    "/{query_id}",
    summary="Update a topic, event or person query"
)
async def update_query_me(
    query_id: int,
    title: str = Query(default=" ", example=" ", description="Title of query to add"),
    description: str = Query(default="", example="", description="Description of query to add"),
    must: list = Query(default=[], example=[], description="MUST words of query"),
    should: list = Query(default=[], example=[], description="SHOULD words of query"),
    must_not: list = Query(default=[], example=[], description="MUST_NOT words of query"),
    img: Optional[UploadFile] = File(None),
    type: int = Query(default=1, example=1, description="1 is Topic, 2 is Person, 3 is Event"),
    current_user: User = Depends(get_current_active_user),
):
    if query_id in current_user.query_ids:

        if query_id <= 73:  # if query_id is less than 73, it means the query is a default query
            query = user_service.create_user_query(
                {
                    "title": title,
                    "description": description,
                    "must": must,
                    "should": should,
                    "must_not": must_not,
                    "query_type": type,
                }
            )
            if img:
                await TelegramService.upload_query_image(query[0]['id'], img)
            current_user.query_ids.append(query[0]['id'])
            current_user.query_ids.remove(query_id)
            user_service.update_user(current_user.id, current_user.model_dump(exclude={'id'}))
            return query[0]

        else:
            new_q = user_service.update_user_query(query_id, data={
                "title": title,
                "description": description,
                "must": must,
                "should": should,
                "must_not": must_not,
                "query_type": type,
            })
            if img:
                await TelegramService.upload_query_image(query_id, img)
            return new_q
    else:
        raise HTTPException(status_code=400, detail=f"Invalid query_id: {query_id}")

@router.delete(
    "/{query_id}",
    summary="Delete a query"
)
async def delete_query_me(
    query_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if query_id in current_user.query_ids:
        current_user.query_ids.remove(query_id)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid query_id: {query_id}")

    return user_service.update_user(current_user.id, current_user.model_dump(exclude={'id'}))
