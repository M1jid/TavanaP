"""
RSS Resources Service
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import RSSResource
from schemas import RSSResourceCreate, RSSResourceUpdate


class RSSResourcesService:
    """Service for RSS resources operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_resources(self) -> List[RSSResource]:
        """Get all RSS resources"""
        return self.db.query(RSSResource).all()
    
    async def get_resource_by_id(self, resource_id: int) -> Optional[RSSResource]:
        """Get RSS resource by ID"""
        return self.db.query(RSSResource).filter(RSSResource.id == resource_id).first()
    
    async def create_resources(self, resources_data: List[RSSResourceCreate]) -> List[RSSResource]:
        """Create new RSS resources"""
        db_resources = []
        for resource_data in resources_data:
            db_resource = RSSResource(**resource_data.dict())
            self.db.add(db_resource)
            db_resources.append(db_resource)
        
        self.db.commit()
        for resource in db_resources:
            self.db.refresh(resource)
        
        return db_resources
    
    async def update_resource(self, resource: RSSResource, resource_data: RSSResourceUpdate) -> RSSResource:
        """Update an existing RSS resource"""
        if resource_data is None:
            return resource
        
        update_data = resource_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(resource, field):
                setattr(resource, field, value)
        
        self.db.commit()
        self.db.refresh(resource)
        return resource
    
    async def delete_resource(self, resource: RSSResource) -> None:
        """Delete a RSS resource"""
        self.db.delete(resource)
        self.db.commit() 