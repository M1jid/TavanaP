"""
Telegram Peers Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import TelegramPeer
import schemas

from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TelegramPeersService:
    """Service for telegram peer operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_peers(self) -> List[TelegramPeer]:
        """Get all telegram peers"""
        return self.db.query(TelegramPeer).all()
    
    async def get_peer_by_id(self, peer_id: int) -> Optional[TelegramPeer]:
        """Get telegram peer by ID"""
        return self.db.query(TelegramPeer).filter(TelegramPeer.id == peer_id).first()
    

    async def get_peers_by_subscriber(self, subscriber: str):
        """Get telegram peers by subscriber"""
        return self.db.query(TelegramPeer).filter(TelegramPeer.subscriber == subscriber).all()

    async def find_peer(
        self,
        id: int | None = None,
        peer_id: int | None = None,
        subscriber: int | None = None,
        username: str | None = None,
        url: str | None = None,
    ) -> TelegramPeer | None:
        """Find telegram peer"""
        param_mapping = {
            'id': TelegramPeer.id,
            'peer_id': TelegramPeer.peer_id,
            'username': TelegramPeer.username,
            'url': TelegramPeer.url,
        }

        if subscriber is not None:
            logger.info(f"Finding peers by subscriber: {subscriber}")
            return await self.get_peers_by_subscriber(subscriber)

        # Otherwise, check other parameters
        for param_name, param_value in {
            "id": id,
            "peer_id": peer_id,
            "username": username,
            "url": url
        }.items():
            if param_value is not None:
                logger.info(f"Finding peer by {param_name}={param_value}")
                return self.db.query(TelegramPeer).filter(
                    param_mapping[param_name] == param_value
                ).first()

        return None

    # async def find_peer(self, **kwargs) -> Optional[TelegramPeer]:
    #     """Find telegram peer by various parameters"""
    #     # Filter out None values
    #     filters = {k: v for k, v in kwargs.items() if v is not None}
        
    #     if not filters:
    #         return None
        
    #     # Build query with filters
    #     query = self.db.query(TelegramPeer)
    #     for field, value in filters.items():
    #         if hasattr(TelegramPeer, field):
    #             query = query.filter(getattr(TelegramPeer, field) == value)
        
    #     return query.first()
    
    async def create_peer(self, peer_data: schemas.TelegramPeerCreate) -> TelegramPeer:
        """Create a new telegram peer"""
        # Check if peer with same peer_id already exists
        if peer_data.peer_id:
            existing_peer = self.db.query(TelegramPeer).filter(
                TelegramPeer.peer_id == peer_data.peer_id
            ).first()
            
            if existing_peer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Peer already exists'
                )
        
        # Create new peer
        db_peer = TelegramPeer(**peer_data.dict())
        self.db.add(db_peer)
        self.db.commit()
        self.db.refresh(db_peer)
        return schemas.TelegramPeer.model_validate(db_peer)
    
    async def update_telegram_peer(self, peer: TelegramPeer, peer_data: schemas.TelegramPeerUpdate) -> TelegramPeer:
        """Update an existing telegram peer"""
        if peer_data is None:
            return peer
        
        update_data = peer_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(peer, field):
                setattr(peer, field, value)
        
        self.db.commit()
        self.db.refresh(peer)
        return schemas.TelegramPeer.model_validate(peer)
    
    async def delete_peer(self, peer: TelegramPeer) -> None:
        """Delete a telegram peer"""
        self.db.delete(peer)
        self.db.commit() 
    
    async def block_telegram_peer(self, peer: TelegramPeer) -> TelegramPeer:
        """Block a telegram peer"""
        peer.blocked = True
        self.db.commit()
        self.db.refresh(peer)
        return schemas.TelegramPeer.model_validate(peer)

    async def unblock_telegram_peer(self, peer: TelegramPeer) -> TelegramPeer:
        """Block a telegram peer"""
        peer.blocked = False
        self.db.commit()
        self.db.refresh(peer)
        return schemas.TelegramPeer.model_validate(peer)

    async def free_telegram_peer(self, subscriber):
        """Drop all telegram peers witch subscribed by subscriber"""
        peers = self.db.query(TelegramPeer).filter(TelegramPeer.subscriber == subscriber).all()
        for peer in peers:
            peer.subscriber = 1
            self.db.commit()
            self.db.refresh(peer)
        return [schemas.TelegramPeer.model_validate(peer) for peer in peers]

    async def subscribe_telegram_peer(self, subscriber):
        next_peer = self.db.query(TelegramPeer)\
        .filter((TelegramPeer.subscriber == 1) & (TelegramPeer.blocked == False))\
        .first()

        if next_peer:
            next_peer.subscriber = subscriber
            self.db.commit()
            self.db.refresh(next_peer)
            return schemas.TelegramPeer.model_validate(next_peer)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No peer available to subscribe"
        )

    async def unsubscribe_telegram_peer(self, peer: TelegramPeer) -> TelegramPeer:
        peer.subscriber = None
        self.db.commit()
        self.db.refresh(peer)
        return schemas.TelegramPeer.model_validate(peer)
