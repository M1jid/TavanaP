"""
Telegram Peer Service

This service handles all database operations related to Telegram peers,
including allocation, subscription management, and peer lifecycle operations.
"""

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from app.models.telegram_peer import TelegramPeer
from app.startup import postgres_engine
from contextlib import contextmanager
from typing import List, Optional

# Logging
import logging
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)


@contextmanager
def acquire_telegram_peer(subscriber: int):
    """Acquire a telegram peer for a subscriber."""
    session = SessionLocal()
    try:
        stmt = (
            select(TelegramPeer)
            .where(TelegramPeer.subscriber == 1, TelegramPeer.blocked == False)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        peer = session.execute(stmt).scalars().one_or_none()

        if peer is None:
            logger.warning("⚠️ No available peers left.")
            yield None
            return

        peer.subscriber = subscriber
        session.commit()
        yield peer 
    finally:
        session.close()


def get_all_subscribed_peers(subscriber: int) -> List[TelegramPeer]:
    """Get all peers subscribed by a specific subscriber."""
    with SessionLocal() as session:
        return session.query(TelegramPeer).filter(TelegramPeer.subscriber == subscriber).all()


def get_peer_by_peer_id(peer_id: int) -> Optional[TelegramPeer]:
    """Get a peer by its peer ID."""
    with SessionLocal() as session:
        return session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).one_or_none()


def get_peer_by_username(username: str) -> Optional[TelegramPeer]:
    """Get a peer by its username."""
    with SessionLocal() as session:
        return session.query(TelegramPeer).filter(TelegramPeer.username == username).one_or_none()


def update_peer(peer_id: int, peer_data: dict) -> Optional[TelegramPeer]:
    """Update peer data."""
    with SessionLocal() as session:
        peer = session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).one_or_none()
        if not peer:
            return None
        for key, value in peer_data.items():
            if hasattr(TelegramPeer, key):
                setattr(peer, key, value)
        session.commit()
        session.refresh(peer)
        return TelegramPeer.model_validate(peer)


def create_peer(peer_data: dict) -> Optional[TelegramPeer]:
    """Create a new peer."""
    with SessionLocal() as session:
        peer = TelegramPeer(**peer_data)
        session.add(peer)
        session.commit()
        session.refresh(peer)
        return TelegramPeer.model_validate(peer)

def get_all_active_peers(subscriber: int) -> List[TelegramPeer]:
    """Get all active peers for a subscriber."""
    with SessionLocal() as session:
        return session.query(TelegramPeer).filter(
            TelegramPeer.subscriber == subscriber,
            TelegramPeer.blocked == False,
            TelegramPeer.on_waiting == False
        ).all()


def unsubscribe_but_joinable_by_peer_id(peer_id: int) -> None:
    """Unsubscribe a peer but keep it joinable."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'subscriber': 1})
        session.commit()


def unsubscribe_but_joinable_by_phone(subscriber: int) -> None:
    """Unsubscribe all peers for a subscriber but keep them joinable."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.subscriber == subscriber).update({'subscriber': 1})
        session.commit()


def unsubscribe_peer(peer_id: int) -> None:
    """Unsubscribe a peer completely."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'subscriber': None})
        session.commit()


def wait_for_peer(peer_id: int) -> None:
    """Set a peer to waiting status."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'on_waiting': True})
        session.commit()


def unwait_for_peer(peer_id: int) -> None:
    """Remove waiting status from a peer."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'on_waiting': False})
        session.commit()


def block_peer(peer_id: int) -> None:
    """Block a peer."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'blocked': True})
        session.commit()


def unblock_peer(peer_id: int) -> None:
    """Unblock a peer."""
    with SessionLocal() as session:
        session.query(TelegramPeer).filter(TelegramPeer.peer_id == peer_id).update({'blocked': False})
        session.commit()
