from fastapi import APIRouter, Depends, HTTPException
from auth.auth import get_current_active_user, User
from schemas import user_schema as schemas
from services import services
from utils import db_handler as db

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/admin_user", tags=["Actions Admin"])
import logging
logger = logging.getLogger(__name__)


@router.get(
    "",
    summary="Get All Users",
)
async def get_all_users(
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    users = db.get_users()
    for user in users:
        del user['hashed_password']
    return users

@router.put(
    "",
    summary="Update any user",
)
async def update_user(
    user_id: int,
    user_data: schemas.RootUpdateUser,
    current_user: User = Depends(get_current_active_user)
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    if user_data.password:
        hashed_password = pwd_context.hash(user_data.password)
    user_date = user_data.model_dump(exclude={'password'})
    user_date['hashed_password'] = hashed_password
    res = db.update_user(user_id, user_date)
    logger.info(f"Updated user: {res}")
    del res['hashed_password']
    return res

@router.put(
    "/status/toggle/{user_id}",
    summary="Toggle any user status"
)
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot toggle your own status")
    return db.toggle_user_status(user_id)

@router.post(
    "",
    summary="Create a new user"
)
async def create_user(
    payload: schemas.CreateUser,
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)

    hashed_password = pwd_context.hash(payload.password)
    payload = payload.model_dump(exclude={'password'})
    payload['hashed_password'] = hashed_password
    return db.create_user(payload)

@router.delete(
    "/{user_id}",
    summary="Delete a user"
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
):
    perm = "admin"
    services.check_access(user=current_user, permission=perm)
    return db.delete_user(user_id)
