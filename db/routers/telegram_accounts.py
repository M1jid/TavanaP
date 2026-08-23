"""
Telegram Accounts API Router
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Query, Path, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.telegram_accounts import TelegramAccountsService
from schemas import TelegramAccount, TelegramAccountCreate, TelegramAccountUpdate

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/accounts", 
    response_model=List[TelegramAccount],
    summary="Get all telegram accounts",
    description="Get all telegram accounts"
)
async def get_all_telegram_accounts(db: Session = Depends(get_db)):
    """Get all telegram accounts"""
    async with db_lock:
        service = TelegramAccountsService(db)
        return await service.get_all_accounts()


@router.get(
    "/accounts/{account_id}", 
    response_model=TelegramAccount,
    summary="Get telegram account by ID",
    description="Get a specific telegram account by ID"
)
async def get_telegram_account_by_id(
    account_id: int = Path(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get telegram account by ID"""
    async with db_lock:
        service = TelegramAccountsService(db)
        account = await service.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account does not exist")
        return account


@router.post(
    "/accounts",
    response_model=List[TelegramAccount],
    summary="Create telegram accounts",
    description="Create new telegram accounts"
)
async def create_telegram_accounts(
    accounts_data: List[TelegramAccountCreate],
    db: Session = Depends(get_db)
):
    """Create new telegram accounts"""
    async with db_lock:
        service = TelegramAccountsService(db)
        return await service.create_accounts(accounts_data)


@router.delete(
    "/accounts/{account_id}",
    summary="Delete telegram account",
    description="Delete a telegram account by ID"
)
async def delete_telegram_account(
    account_id: int = Path(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Delete a telegram account"""
    async with db_lock:
        service = TelegramAccountsService(db)
        account = await service.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account does not exist")
        
        await service.delete_account(account)
        return "successfully deleted the account"


@router.put(
    "/accounts/{account_id}", 
    response_model=TelegramAccount,
    summary="Update telegram account",
    description="Update an existing telegram account"
)
async def update_telegram_account(
    account_id: int = Path(..., description="Account ID to update"),
    account_data: TelegramAccountUpdate = None,
    db: Session = Depends(get_db)
):
    """Update a telegram account"""
    async with db_lock:
        service = TelegramAccountsService(db)
        account = await service.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account does not exist")
        
        return await service.update_account(account, account_data)


@router.get(
    "/accounts/process/up",
    response_model=TelegramAccount,
    summary="Get next available account for processing",
    description="Get the next available telegram account for processing"
)
async def get_next_available_account(db: Session = Depends(get_db)):
    """Get next available account for processing"""
    async with db_lock:
        service = TelegramAccountsService(db)
        return await service.get_next_available_account()


@router.put(
    "/accounts/process/down/{account_id}", 
    response_model=TelegramAccount,
    summary="Mark account as not processing",
    description="Mark a telegram account as not currently processing"
)
async def mark_account_not_processing(
    account_id: int = Path(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Mark account as not processing"""
    async with db_lock:
        service = TelegramAccountsService(db)
        account = await service.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account does not exist")
        
        return await service.mark_account_not_processing(account) 