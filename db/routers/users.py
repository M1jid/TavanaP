"""
Users API Router
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.users import UsersService
from schemas import User, UserCreate, UserUpdate

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/users", 
    response_model=List[User] | User,
    summary="Get users",
    description="Get all users or a specific user by various parameters"
)
async def get_user(
    id: Optional[int] = Query(None, description="User ID"),
    username: Optional[str] = Query(None, description="Username"),
    email: Optional[str] = Query(None, description="Email"),
    disabled: Optional[bool] = Query(None, description="Disabled status"),
    db: Session = Depends(get_db)
):
    """Get users with optional filtering"""
    async with db_lock:
        service = UsersService(db)
        
        # If any parameter is provided, find specific user
        if any([id, username, email]):
            user = await service.find_user(
                id=id, username=username, email=email
            )
            if not user:
                raise HTTPException(status_code=404, detail="User does not exist")
            return user
        else:
            # Return all users if no specific parameter provided
            return await service.get_all_users(disabled=disabled)


@router.post(
    "/users",
    response_model=User,
    summary="Create user",
    description="Create a new user"
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    async with db_lock:
        service = UsersService(db)
        return await service.create_user(user_data)


@router.put(
    "/users/{id}", 
    response_model=User,
    summary="Update user",
    description="Update an existing user"
)
async def update_user(
    id: int ,
    user_data: UserUpdate = None,
    db: Session = Depends(get_db)
):
    """Update a user"""
    async with db_lock:
        service = UsersService(db)
        user = await service.get_user_by_id(id)
        if not user:
            raise HTTPException(status_code=404, detail="User does not exist")
        
        return await service.update_user(user, user_data)


@router.put(
    "/users/status/toggle/{id}", 
    response_model=User,
    summary="Update user",
    description="Update an existing user"
)
async def update_user(
    id: int ,
    db: Session = Depends(get_db)
):
    """Update a user"""
    async with db_lock:
        service = UsersService(db)
        user = await service.get_user_by_id(id)
        if not user:
            raise HTTPException(status_code=404, detail="User does not exist")
        
        return await service.toggle_status(user)


@router.delete(
    "/users/{id}",
    summary="Delete user",
    description="Delete a user"
)
async def delete_user(
    id: int,
    # username: Optional[str] = Query(None, description="Username"),
    # email: Optional[str] = Query(None, description="Email"),
    db: Session = Depends(get_db)
):
    """Delete a user"""
    async with db_lock:
        service = UsersService(db)
        
        user = await service.find_user(
            id=id #, username=username, email=email
        )
        if not user:
            raise HTTPException(status_code=404, detail="User does not exist")

        await service.delete_user(user)
        return "successfully deleted the user" 