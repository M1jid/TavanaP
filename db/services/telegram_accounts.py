"""
Telegram Accounts Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import TelegramAccount
import schemas

class TelegramAccountsService:
    """Service for telegram accounts operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_accounts(self) -> List[TelegramAccount]:
        """Get all telegram accounts"""
        return self.db.query(TelegramAccount).all()
    
    async def get_account_by_id(self, account_id: int) -> Optional[TelegramAccount]:
        """Get telegram account by ID"""
        return self.db.query(TelegramAccount).filter(TelegramAccount.id == account_id).first()
    
    async def create_accounts(self, accounts_data: List[schemas.TelegramAccountCreate]) -> List[TelegramAccount]:
        """Create new telegram accounts"""
        db_accounts = []
        for account_data in accounts_data:
            db_account = TelegramAccount(**account_data.dict())
            self.db.add(db_account)
            db_accounts.append(db_account)
        
        self.db.commit()
        for account in db_accounts:
            self.db.refresh(account)
        
        return db_accounts
    
    async def update_account(self, account: TelegramAccount, account_data: schemas.TelegramAccountUpdate) -> TelegramAccount:
        """Update an existing telegram account"""
        if account_data is None:
            return account
        
        update_data = account_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(account, field):
                setattr(account, field, value)
        
        self.db.commit()
        self.db.refresh(account)
        return account
    
    async def delete_account(self, account: TelegramAccount) -> None:
        """Delete a telegram account"""
        self.db.delete(account)
        self.db.commit()
    
    async def get_next_available_account(self) -> Optional[TelegramAccount]:
        """Get next available account for processing"""
        next_account = self.db.query(TelegramAccount).filter(TelegramAccount.process == 0).first()
        if next_account:
            next_account.process = 1
            self.db.commit()
            self.db.refresh(next_account)
            return schemas.TelegramAccount.model_validate(next_account)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'No free account available'
        )
    
    async def mark_account_not_processing(self, account: TelegramAccount) -> TelegramAccount:
        """Mark account as not processing"""
        account.process = 0
        self.db.commit()
        self.db.refresh(account)
        return schemas.TelegramAccount.model_validate(account)
