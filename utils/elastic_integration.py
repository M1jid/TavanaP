"""
Integration example for using ElasticHandler in FastAPI endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from elastic_handler import ElasticHandler
from elastic_config import get_elastic_config

# Initialize Elasticsearch handler
elastic_config = get_elastic_config()
elastic_handler = ElasticHandler(**elastic_config)

router = APIRouter(prefix="/elastic", tags=["Elasticsearch Operations"])

# Pydantic models for request/response
class IndexCreateRequest(BaseModel):
    index_name: str
    body: Dict[str, Any]
    check_exists: bool = True

class DocumentIndexRequest(BaseModel):
    index_name: str
    document: Dict[str, Any]
    document_id: Optional[str] = None

class BulkIndexRequest(BaseModel):
    index_name: str
    documents: List[Dict[str, Any]]
    document_ids: Optional[List[str]] = None

class SearchRequest(BaseModel):
    index_name: str
    query: Dict[str, Any]
    size: int = 10
    from_: int = 0

class DocumentUpdateRequest(BaseModel):
    index_name: str
    document_id: str
    update_data: Dict[str, Any]


@router.post("/create-index")
async def create_index(request: IndexCreateRequest):
    """
    Create an index in Elasticsearch.
    
    Args:
        request: IndexCreateRequest containing index details
    
    Returns:
        JSON response with index creation status
    """
    try:
        success = elastic_handler.create_index(
            request.index_name,
            request.body,
            check_exists=request.check_exists
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Index '{request.index_name}' created successfully",
                "index_name": request.index_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create index '{request.index_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating index: {str(e)}"
        )


@router.delete("/delete-index/{index_name}")
async def delete_index(index_name: str):
    """
    Delete an index from Elasticsearch.
    
    Args:
        index_name: Name of the index to delete
    
    Returns:
        JSON response with index deletion status
    """
    try:
        success = elastic_handler.delete_index(index_name)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Index '{index_name}' deleted successfully",
                "index_name": index_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting index: {str(e)}"
        )


@router.get("/index-exists/{index_name}")
async def index_exists(index_name: str):
    """
    Check if an index exists.
    
    Args:
        index_name: Name of the index to check
    
    Returns:
        JSON response with index existence status
    """
    try:
        exists = elastic_handler.index_exists(index_name)
        return JSONResponse({
            "success": True,
            "index_name": index_name,
            "exists": exists
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking index existence: {str(e)}"
        )


@router.post("/ensure-index")
async def ensure_index(request: IndexCreateRequest):
    """
    Ensure an index exists, create if it doesn't.
    
    Args:
        request: IndexCreateRequest containing index details
    
    Returns:
        JSON response with index status
    """
    try:
        success = elastic_handler.ensure_index_exists(
            request.index_name,
            request.body
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Index '{request.index_name}' exists or was created successfully",
                "index_name": request.index_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ensure index '{request.index_name}' exists"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ensuring index exists: {str(e)}"
        )


@router.post("/index-document")
async def index_document(request: DocumentIndexRequest):
    """
    Index a document in Elasticsearch.
    
    Args:
        request: DocumentIndexRequest containing document details
    
    Returns:
        JSON response with document indexing status
    """
    try:
        document_id = elastic_handler.index_document(
            request.index_name,
            request.document,
            request.document_id
        )
        
        if document_id:
            return JSONResponse({
                "success": True,
                "message": f"Document indexed successfully in index '{request.index_name}'",
                "index_name": request.index_name,
                "document_id": document_id,
                "document": request.document
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to index document in index '{request.index_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error indexing document: {str(e)}"
        )


@router.post("/bulk-index")
async def bulk_index(request: BulkIndexRequest):
    """
    Bulk index multiple documents in Elasticsearch.
    
    Args:
        request: BulkIndexRequest containing documents details
    
    Returns:
        JSON response with bulk indexing status
    """
    try:
        result = elastic_handler.bulk_index(
            request.index_name,
            request.documents,
            request.document_ids
        )
        
        return JSONResponse({
            "success": True,
            "message": f"Bulk indexing completed for index '{request.index_name}'",
            "index_name": request.index_name,
            "success_count": result.get('success_count', 0),
            "error_count": result.get('error_count', 0),
            "errors": result.get('errors', [])
        })
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error bulk indexing documents: {str(e)}"
        )


@router.get("/get-document/{index_name}/{document_id}")
async def get_document(index_name: str, document_id: str):
    """
    Get a document by ID.
    
    Args:
        index_name: Name of the index
        document_id: Document ID
    
    Returns:
        JSON response with document data
    """
    try:
        document = elastic_handler.get_document_by_id(index_name, document_id)
        if document:
            return JSONResponse({
                "success": True,
                "index_name": index_name,
                "document_id": document_id,
                "document": document
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found in index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document: {str(e)}"
        )


@router.post("/search-documents")
async def search_documents(request: SearchRequest):
    """
    Search documents in an index.
    
    Args:
        request: SearchRequest containing search details
    
    Returns:
        JSON response with search results
    """
    try:
        results = elastic_handler.search_documents(
            request.index_name,
            request.query,
            request.size,
            request.from_
        )
        
        if results:
            total_hits = results.get('hits', {}).get('total', {}).get('value', 0)
            hits = results.get('hits', {}).get('hits', [])
            
            return JSONResponse({
                "success": True,
                "index_name": request.index_name,
                "total_hits": total_hits,
                "hits": hits,
                "query": request.query
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed for index '{request.index_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )


@router.put("/update-document")
async def update_document(request: DocumentUpdateRequest):
    """
    Update a document in Elasticsearch.
    
    Args:
        request: DocumentUpdateRequest containing update details
    
    Returns:
        JSON response with update status
    """
    try:
        success = elastic_handler.update_document(
            request.index_name,
            request.document_id,
            request.update_data
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Document '{request.document_id}' updated successfully in index '{request.index_name}'",
                "index_name": request.index_name,
                "document_id": request.document_id,
                "update_data": request.update_data
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update document '{request.document_id}' in index '{request.index_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating document: {str(e)}"
        )


@router.delete("/delete-document/{index_name}/{document_id}")
async def delete_document(index_name: str, document_id: str):
    """
    Delete a document from Elasticsearch.
    
    Args:
        index_name: Name of the index
        document_id: Document ID
    
    Returns:
        JSON response with deletion status
    """
    try:
        success = elastic_handler.delete_document(index_name, document_id)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Document '{document_id}' deleted successfully from index '{index_name}'",
                "index_name": index_name,
                "document_id": document_id
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document '{document_id}' from index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/list-indices")
async def list_indices():
    """
    List all indices in Elasticsearch.
    
    Returns:
        JSON response with list of indices
    """
    try:
        indices = elastic_handler.list_indices()
        return JSONResponse({
            "success": True,
            "indices": indices,
            "count": len(indices)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing indices: {str(e)}"
        )


@router.get("/index-count/{index_name}")
async def get_index_count(index_name: str):
    """
    Get document count for an index.
    
    Args:
        index_name: Name of the index
    
    Returns:
        JSON response with document count
    """
    try:
        count = elastic_handler.get_index_count(index_name)
        if count is not None:
            return JSONResponse({
                "success": True,
                "index_name": index_name,
                "count": count
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get count for index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting index count: {str(e)}"
        )


@router.get("/index-status/{index_name}")
async def get_index_status(index_name: str):
    """
    Get detailed status information for an index.
    
    Args:
        index_name: Name of the index
    
    Returns:
        JSON response with index status
    """
    try:
        status = elastic_handler.get_index_status(index_name)
        if status:
            return JSONResponse({
                "success": True,
                "index_name": index_name,
                "status": status
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get status for index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting index status: {str(e)}"
        )


@router.get("/cluster-health")
async def get_cluster_health():
    """
    Get cluster health information.
    
    Returns:
        JSON response with cluster health
    """
    try:
        health = elastic_handler.get_cluster_health()
        if health:
            return JSONResponse({
                "success": True,
                "health": health
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to get cluster health"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cluster health: {str(e)}"
        )


@router.get("/cluster-info")
async def get_cluster_info():
    """
    Get cluster information.
    
    Returns:
        JSON response with cluster info
    """
    try:
        info = elastic_handler.get_cluster_info()
        if info:
            return JSONResponse({
                "success": True,
                "info": info
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to get cluster info"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cluster info: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Perform a health check on the Elasticsearch cluster.
    
    Returns:
        JSON response with health status
    """
    try:
        is_healthy = elastic_handler.health_check()
        cluster_info = elastic_handler.get_cluster_info()
        
        return JSONResponse({
            "success": True,
            "healthy": is_healthy,
            "cluster_info": cluster_info
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during health check: {str(e)}"
        )


@router.post("/refresh-index/{index_name}")
async def refresh_index(index_name: str):
    """
    Refresh an index to make recent changes visible.
    
    Args:
        index_name: Name of the index to refresh
    
    Returns:
        JSON response with refresh status
    """
    try:
        success = elastic_handler.refresh_index(index_name)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Index '{index_name}' refreshed successfully",
                "index_name": index_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing index: {str(e)}"
        )


@router.post("/flush-index/{index_name}")
async def flush_index(index_name: str):
    """
    Flush an index to persist changes to disk.
    
    Args:
        index_name: Name of the index to flush
    
    Returns:
        JSON response with flush status
    """
    try:
        success = elastic_handler.flush_index(index_name)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Index '{index_name}' flushed successfully",
                "index_name": index_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to flush index '{index_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error flushing index: {str(e)}"
        )


# Utility functions for common operations
def create_user_index(user_id: str, user_data: Dict[str, Any]) -> Optional[str]:
    """
    Create a user index and index user data.
    
    Args:
        user_id: User identifier
        user_data: User data to index
        
    Returns:
        str: Document ID if successful, None otherwise
    """
    try:
        # Create index if it doesn't exist
        index_name = f"users_{user_id}"
        index_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "username": {"type": "text"},
                    "email": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        success = elastic_handler.ensure_index_exists(index_name, index_config)
        if success:
            # Index the user data
            return elastic_handler.index_document(index_name, user_data, user_id)
        return None
        
    except Exception as e:
        logger.error(f"Error creating user index: {e}")
        return None


def create_log_index(log_data: Dict[str, Any]) -> Optional[str]:
    """
    Create a log index and index log data.
    
    Args:
        log_data: Log data to index
        
    Returns:
        str: Document ID if successful, None otherwise
    """
    try:
        # Create index if it doesn't exist
        index_name = "application_logs"
        index_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "service": {"type": "keyword"},
                    "user_id": {"type": "keyword"}
                }
            }
        }
        
        success = elastic_handler.ensure_index_exists(index_name, index_config)
        if success:
            # Index the log data
            return elastic_handler.index_document(index_name, log_data)
        return None
        
    except Exception as e:
        logger.error(f"Error creating log index: {e}")
        return None


def search_users(query: str, size: int = 10) -> Optional[Dict[str, Any]]:
    """
    Search for users.
    
    Args:
        query: Search query
        size: Number of results to return
        
    Returns:
        Dict: Search results or None if failed
    """
    try:
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["username", "email"],
                    "type": "best_fields"
                }
            }
        }
        
        return elastic_handler.search_documents("users_*", search_query, size)
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return None 
