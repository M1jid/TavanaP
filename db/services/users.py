"""
Users Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import User
from schemas import UserCreate, UserUpdate

from fastapi import HTTPException, status
from schemas import users as schemas

class UsersService:
    """Service for user operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_users(self, disabled: Optional[bool] = None) -> List[User]:
        """Get all users with optional disabled filter"""
        query = self.db.query(User)
        if disabled is not None:
            query = query.filter(User.disabled == disabled)
        return query.all()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def find_user(self, **kwargs) -> Optional[User]:
        """Find user by various parameters"""
        # Filter out None values
        filters = {k: v for k, v in kwargs.items() if v is not None}
        
        if not filters:
            return None
        
        # Build query with filters
        query = self.db.query(User)
        for field, value in filters.items():
            if hasattr(User, field):
                query = query.filter(getattr(User, field) == value)
        
        return query.first()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user with same username already exists
        existing_user = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username {user_data.username} or email {user_data.email} already exists"
            )
        
        # Check if user with same email already exists
        existing_email = self.db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_data.email} already exists"
            )
        
        # Create new user
        db_user = User(**user_data.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    async def update_user(self, user: User, user_data: UserUpdate) -> User:
        """Update an existing user"""
        if user_data is None:
            return user
        
        update_data = user_data.dict(exclude_unset=True)
        
        # Check for duplicate username if updating username
        if 'username' in update_data:
            existing_user = self.db.query(User).filter(
                and_(User.username == update_data['username'], User.id != user.id)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with username {update_data['username']} already exists"
                )
        
        # Check for duplicate email if updating email
        if 'email' in update_data:
            existing_email = self.db.query(User).filter(
                and_(User.email == update_data['email'], User.id != user.id)
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email {update_data['email']} already exists"
                )
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    async def toggle_status(self, user: User) -> User:
        user.disabled = False if user.disabled else True
        self.db.commit()
        self.db.refresh(user)
        return schemas.User.model_validate(user)


    async def delete_user(self, user: User) -> None:
        """Delete a user"""
        self.db.delete(user)
        self.db.commit() 