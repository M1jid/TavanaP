"""
Telegram Peers API Router
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.telegram_peers import TelegramPeersService
from schemas import TelegramPeer, TelegramPeerCreate, TelegramPeerUpdate

router = APIRouter()
db_lock = asyncio.Lock()


async def _find_telegram_peer(service, **kwargs):
    """Helper function to find a telegram peer by various parameters"""
    # Filter out None values and db parameter
    search_params = {k: v for k, v in kwargs.items() if v is not None}
    
    if not search_params:
        return None
    
    # Get the first non-None parameter and its value
    param_name, param_value = next(iter(search_params.items()))
    
    return await service.find_peer(**{param_name: param_value})


@router.get(
    "/peers", 
    response_model=List[TelegramPeer] | TelegramPeer,
    summary="Get telegram peers",
    description="Get all telegram peers or a specific peer by various parameters"
)
async def get_telegram_peer(
    id: Optional[int] = Query(None, description="Peer ID"),
    peer_id: Optional[int] = Query(None, description="Telegram peer ID"),
    subscriber: Optional[int] = Query(None, description="Subscriber ID"),
    username: Optional[str] = Query(None, description="Username"),
    url: Optional[str] = Query(None, description="URL"),
    db: Session = Depends(get_db)
):
    """Get telegram peers with optional filtering"""
    async with db_lock:
        service = TelegramPeersService(db)
        
        # If any parameter is provided, find specific peer
        if any([id, peer_id, subscriber, username, url]):
            peer = await _find_telegram_peer(
                service=service,
                id=id, peer_id=peer_id, subscriber=subscriber, 
                username=username, url=url
            )
            if not peer:
                raise HTTPException(status_code=404, detail="Peer does not exist")
            return peer
        else:
            # Return all peers if no specific parameter provided
            return await service.get_all_peers()


@router.post(
    "/peers",
    response_model=TelegramPeer,
    summary="Create telegram peer",
    description="Create a new telegram peer"
)
async def create_telegram_peer(
    peer_data: TelegramPeerCreate,
    db: Session = Depends(get_db)
):
    """Create a new telegram peer"""
    async with db_lock:
        service = TelegramPeersService(db)
        return await service.create_peer(peer_data)

@router.put(
    "/peers", 
    response_model=TelegramPeer,
)
async def update_telegram_peer(
    peer_data: TelegramPeerUpdate,
    id: Optional[int] = Query(None),
    peer_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)
        peer = await _find_telegram_peer(
            service=service, id=id, peer_id=peer_id, username=username, url=url
        )
        if not peer:
            raise HTTPException(status_code=404, detail="Peer does not exist")

        return await service.update_telegram_peer(
            peer_data=peer_data,
            peer=peer
        )

@router.delete(
    "/peers",
    summary="Delete telegram peer",
    description="Delete a telegram peer"
)
async def delete_telegram_peer(
    id: Optional[int] = Query(None, description="Peer ID"),
    peer_id: Optional[int] = Query(None, description="Telegram peer ID"),
    subscriber: Optional[int] = Query(None, description="Subscriber ID"),
    username: Optional[str] = Query(None, description="Username"),
    url: Optional[str] = Query(None, description="URL"),
    db: Session = Depends(get_db)
):
    """Delete a telegram peer"""
    async with db_lock:
        service = TelegramPeersService(db)
        
        peer = await _find_telegram_peer(
            service=service,
            id=id, peer_id=peer_id, subscriber=subscriber, 
            username=username, url=url
        )
        if not peer:
            raise HTTPException(status_code=404, detail="Peer does not exist")

        await service.delete_peer(peer)
        return "successfully deleted the peer" 


@router.put(
    "/peers/block",
    response_model=TelegramPeer,
)
async def block_telegram_peer(
    id: Optional[int] = Query(None),
    peer_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)

        peer = await _find_telegram_peer(
            service=service, id=id, peer_id=peer_id, username=username, url=url
        )
        if not peer:
            raise HTTPException(status_code=404, detail="Peer does not exist")

        return await service.block_telegram_peer(peer=peer)

@router.put(
    "/peers/unblock",
    response_model=TelegramPeer,
)
async def unblock_telegram_peer(
    id: Optional[int] = Query(None),
    peer_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)

        peer = await _find_telegram_peer(
            service=service, id=id, peer_id=peer_id, username=username, url=url
        )
        if not peer:
            raise HTTPException(status_code=404, detail="Peer does not exist")

        return await service.unblock_telegram_peer(peer=peer)

@router.put(
    "/peers/drop_channels",
    response_model=List[TelegramPeer],
)
async def free_telegram_peer(
    subscriber: int,
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)
        return await service.free_telegram_peer(subscriber=subscriber)


@router.get(
    "/peers/subscribe/{subscriber}", 
    response_model=TelegramPeer,
)
async def subscribe_telegram_peer(
    subscriber: int,
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)

        peer = await service.subscribe_telegram_peer(subscriber=subscriber)
        if not peer:
            raise HTTPException(status_code=404, detail="No peer available to subscribe")
        return peer

@router.put(
    "/peers/unsubscribe", 
    response_model=TelegramPeer,
)
async def unsubscribe_telegram_peer(
    id: Optional[int] = Query(None),
    peer_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = TelegramPeersService(db)

        peer = await _find_telegram_peer(
            service=service, id=id, peer_id=peer_id, username=username, url=url
        )
        if not peer:
            raise HTTPException(status_code=404, detail="Peer does not exist")

        return await service.unsubscribe_telegram_peer(peer=peer)
