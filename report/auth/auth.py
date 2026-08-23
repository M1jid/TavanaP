from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

from utils.db_handler import get_user_by_username

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    disabled: Optional[bool] = False
    history: List[Dict] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    query_ids: List[int] = Field(default_factory=list)

    following_channels: List[int]
    following_groups: List[int]
    following_users: List[int]
    accessible_urls: List[str]

class UserInDB(User):
    hashed_password: str


# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Utility functions
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def get_user(username: str):
    try:
        user_dict = get_user_by_username(username=username)
        return UserInDB(**user_dict)
    except Exception:
        return None


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def check_user_entrance(user, base_url):
    logger.info(base_url)
    hostname = urlparse(str(base_url)).hostname  # e.g. "example.com"
    logger.info(f"Checking {hostname} in {user.accessible_urls}")
    return hostname in user.accessible_urls
    # for url in user.accessible_urls:
    #     if str(base_url) in url:
    #         return True
    # return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
