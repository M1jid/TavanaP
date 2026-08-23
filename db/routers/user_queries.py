"""
Users API Router
"""
import asyncio
from typing import List, Optional, Union
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.user_queries import UsersQueriesService
from schemas import UserQueries, UserQueriesCreate, UserQueriesUpdate

router = APIRouter()
db_lock = asyncio.Lock()


@router.get(
    "/queries", 
    response_model=List[UserQueries] | UserQueries,
    summary="Get all topic, person and event queries",
    description= """
Retrieve all queries (topics, persons, and events) associated with user_query_ids table.  

- **Topic queries** → List of topic-related queries (query_type = 1)
- **Person queries** → List of person-related queries (query_type = 2)
- **Event queries** → List of event-related queries (query_type = 3)

    """,
    response_description="A list of all queries (topics, persons, events)."
)
async def get_user_query(
    db: Session = Depends(get_db)
):
    """Get users with optional filtering"""
    async with db_lock:
        service = UsersQueriesService(db)
        return await service.get_all_users_quries()


@router.get(
    "/queries/{id}", 
    response_model=UserQueries,
    summary="Get a query (topic, person or event) by ID",
    description= """

Retrieve a query (topic, person or event) by its unique ID.   

    """,
    response_description="Details of the query matching the provided ID."
)
async def get_user_query_by_id(
    id: int,
    db: Session = Depends(get_db)
):
    async with db_lock:
        service = UsersQueriesService(db)

        user_query = await service.get_user_quries_by_id(id)
        if not user_query:
            raise HTTPException(status_code=404, detail="User does not exist")
        return user_query

@router.post(
    "/queries",
    response_model=Union[UserQueries, List[UserQueries]],
    summary="Add a new query (topic, person or event)",
    description= """

Add a query (topic, person or event) with its details.   

    """
)
async def create_user_query(
    user_query_data: Union[UserQueriesCreate, List[UserQueriesCreate]],
    db: Session = Depends(get_db)
):
    """Create a new user query or multiple queries"""
    async with db_lock:
        service = UsersQueriesService(db)
        if isinstance(user_query_data, list):
            # multiple queries
            return [await service.create_user_quries(uq) for uq in user_query_data]
        else:
            # single query
            return await service.create_user_quries(user_query_data)


@router.put(
    "/queries/{id}", 
    response_model=UserQueries,
    summary="Update an existing query (topic, person or event) by ID",
    description= """

Update a query (topic, person or event) with its details.   

    """
)
async def update_user_query(
    id: int,
    user_query_data: UserQueriesUpdate = None,
    db: Session = Depends(get_db)
):
    """Update a user"""
    async with db_lock:
        service = UsersQueriesService(db)
        user_query = await service.get_user_quries_by_id(id)
        if not user_query:
            raise HTTPException(status_code=404, detail="User query does not exist")
        
        return await service.update_user_quries(user_query, user_query_data)


@router.delete(
    "/queries/{id}",
    summary="Delete an existing query (topic, person or event) by ID",
    description= """

Delete a query (topic, person or event) with all its details.   

    """
)
async def delete_user_query(
    id: int,
    db: Session = Depends(get_db)
):
    """Delete a user query"""
    async with db_lock:
        service = UsersQueriesService(db)
        
        user_query = await service.get_user_quries_by_id(id)
        if not user_query:
            raise HTTPException(status_code=404, detail="User query does not exist")

        await service.delete_user_quries(user_query)
        return "successfully deleted the user" 