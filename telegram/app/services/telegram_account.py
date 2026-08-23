"""
Telegram Account Service

This service handles all database operations related to Telegram accounts,
including allocation, account lifecycle management, and account status tracking.
"""

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from app.models.telegram_account import TelegramAccount
import logging
from app.startup import postgres_engine
from contextlib import contextmanager

logger = logging.getLogger(__name__)
SessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)


@contextmanager
def acquire_telegram_account():
    """Acquire a telegram account for processing."""
    session = SessionLocal()
    result = None
    try:
        stmt = (
            select(TelegramAccount)
            .where(TelegramAccount.process == 0)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        result = session.execute(stmt).scalars().first()
        if result is None:
            logger.error("⚠️ No available accounts left.")
            yield None
        else:
            result.process = 1
            session.add(result)
            session.commit()
            logger.info(f"✅ Picked account: {result.phone}")
            yield result
    finally:
        session.close()

def drop_account(account_id: int) -> None:
    """Release an account back to the pool."""
    with SessionLocal() as session:
        account = session.query(TelegramAccount).filter(TelegramAccount.id == account_id).one_or_none()
        if account:
            account.process = 0
            session.add(account)
            logger.info(f"✅ Dropped account: {account.phone}")
        session.commit()
