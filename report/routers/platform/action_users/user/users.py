from fastapi import APIRouter, Depends, HTTPException
from auth.auth import get_current_active_user, User
from schemas import user_schema as schemas
from utils import db_handler as db


from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user/me", tags=["Actions User"])


@router.get(
    "",
    summary="Get current user",
)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    return current_user.model_dump(exclude={'hashed_password'})

@router.put(
    "",
    summary="Update current user",
)
async def update_current_user(
    user_data: schemas.RegularUpdateUser,
    current_user: User = Depends(get_current_active_user),
):
    if user_data.password:
        hashed_password = pwd_context.hash(user_data.password)
    user_date = user_data.model_dump(exclude={'password'})
    user_date['hashed_password'] = hashed_password
    res = db.update_user(current_user.id, user_date)
    logger.info(f"Updated user: {res}")
    del res['hashed_password']
    return res
