"""
RSS Resources API Router
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Query, Path, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.rss_resources import RSSResourcesService
from schemas import RSSResource, RSSResourceCreate, RSSResourceUpdate

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/rss/channels", 
    # response_model=List[RSSResource],
    summary="Get all RSS resources",
    description="Get all RSS resources"
)
async def get_all_rss_resources(db: Session = Depends(get_db)):
    """Get all RSS resources"""
    async with db_lock:
        service = RSSResourcesService(db)
        return await service.get_all_resources()


@router.get(
    "/rss/channels/{channel_id}", 
    # response_model=RSSResource,
    summary="Get RSS resource by ID",
    description="Get a specific RSS resource by ID"
)
async def get_rss_resource_by_id(
    channel_id: int = Path(..., description="Channel ID"),
    db: Session = Depends(get_db)
):
    """Get RSS resource by ID"""
    async with db_lock:
        service = RSSResourcesService(db)
        resource = await service.get_resource_by_id(channel_id)
        if not resource:
            raise HTTPException(status_code=404, detail="RSS resource does not exist")
        return resource


@router.post(
    "/rss/channels",
    # response_model=List[RSSResource],
    summary="Create RSS resources",
    description="Create new RSS resources"
)
async def create_rss_resources(
    resources_data: List[RSSResourceCreate],
    db: Session = Depends(get_db)
):
    """Create new RSS resources"""
    async with db_lock:
        service = RSSResourcesService(db)
        return await service.create_resources(resources_data)


@router.delete(
    "/rss/channels/{channel_id}",
    summary="Delete RSS resource",
    description="Delete a RSS resource by ID"
)
async def delete_rss_resource(
    channel_id: int = Path(..., description="Channel ID"),
    db: Session = Depends(get_db)
):
    """Delete a RSS resource"""
    async with db_lock:
        service = RSSResourcesService(db)
        resource = await service.get_resource_by_id(channel_id)
        if not resource:
            raise HTTPException(status_code=404, detail="RSS resource does not exist")
        
        await service.delete_resource(resource)
        return "successfully deleted the RSS resource"


@router.put(
    "/rss/channels/{channel_id}", 
    # response_model=RSSResource,
    summary="Update RSS resource",
    description="Update an existing RSS resource"
)
async def update_rss_resource(
    channel_id: int = Path(..., description="Channel ID to update"),
    resource_data: RSSResourceUpdate = None,
    db: Session = Depends(get_db)
):
    """Update a RSS resource"""
    async with db_lock:
        service = RSSResourcesService(db)
        resource = await service.get_resource_by_id(channel_id)
        if not resource:
            raise HTTPException(status_code=404, detail="RSS resource does not exist")
        
        return await service.update_resource(resource, resource_data) 