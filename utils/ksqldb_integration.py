"""
Integration example for using KsqlDBHandler in FastAPI endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from ksqldb_handler import KsqlDBHandler
from ksqldb_config import get_ksqldb_config

# Initialize ksqlDB handler
ksqldb_config = get_ksqldb_config()
ksqldb_handler = KsqlDBHandler(**ksqldb_config)

router = APIRouter(prefix="/ksqldb", tags=["ksqlDB Operations"])

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    stream_properties: Optional[Dict[str, Any]] = None

class StreamCreateRequest(BaseModel):
    stream_name: str
    stream_config: str
    check_exists: bool = True

class TableCreateRequest(BaseModel):
    table_name: str
    table_config: str
    check_exists: bool = True

class ConnectorCreateRequest(BaseModel):
    connector_name: str
    connector_config: str
    check_exists: bool = True

class DataInsertRequest(BaseModel):
    stream_name: str
    data: Dict[str, Any]


@router.post("/execute-query")
async def execute_query(request: QueryRequest):
    """
    Execute a ksqlDB query.
    
    Args:
        request: QueryRequest containing the query and optional stream properties
    
    Returns:
        JSON response with query execution result
    """
    try:
        result = ksqldb_handler.execute_query(
            request.query,
            stream_properties=request.stream_properties
        )
        
        if result is not None:
            return JSONResponse({
                "success": True,
                "result": result,
                "query": request.query
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to execute ksqlDB query"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing query: {str(e)}"
        )


@router.post("/create-stream")
async def create_stream(request: StreamCreateRequest):
    """
    Create a stream in ksqlDB.
    
    Args:
        request: StreamCreateRequest containing stream details
    
    Returns:
        JSON response with stream creation status
    """
    try:
        success = ksqldb_handler.create_stream(
            request.stream_name,
            request.stream_config,
            check_exists=request.check_exists
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Stream '{request.stream_name}' created successfully",
                "stream_name": request.stream_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create stream '{request.stream_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating stream: {str(e)}"
        )


@router.post("/create-table")
async def create_table(request: TableCreateRequest):
    """
    Create a table in ksqlDB.
    
    Args:
        request: TableCreateRequest containing table details
    
    Returns:
        JSON response with table creation status
    """
    try:
        success = ksqldb_handler.create_table(
            request.table_name,
            request.table_config,
            check_exists=request.check_exists
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Table '{request.table_name}' created successfully",
                "table_name": request.table_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create table '{request.table_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating table: {str(e)}"
        )


@router.post("/create-connector")
async def create_connector(request: ConnectorCreateRequest):
    """
    Create a sink connector in ksqlDB.
    
    Args:
        request: ConnectorCreateRequest containing connector details
    
    Returns:
        JSON response with connector creation status
    """
    try:
        success = ksqldb_handler.create_sink_connector(
            request.connector_name,
            request.connector_config,
            check_exists=request.check_exists
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Connector '{request.connector_name}' created successfully",
                "connector_name": request.connector_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create connector '{request.connector_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating connector: {str(e)}"
        )


@router.post("/insert-data")
async def insert_data(request: DataInsertRequest):
    """
    Insert data into a ksqlDB stream.
    
    Args:
        request: DataInsertRequest containing stream name and data
    
    Returns:
        JSON response with data insertion status
    """
    try:
        success = ksqldb_handler.insert_data(
            request.stream_name,
            request.data
        )
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Data inserted successfully into stream '{request.stream_name}'",
                "stream_name": request.stream_name,
                "data": request.data
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to insert data into stream '{request.stream_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting data: {str(e)}"
        )


@router.get("/list-streams")
async def list_streams():
    """
    List all streams in ksqlDB.
    
    Returns:
        JSON response with list of streams
    """
    try:
        streams = ksqldb_handler.list_streams()
        return JSONResponse({
            "success": True,
            "streams": streams,
            "count": len(streams)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing streams: {str(e)}"
        )


@router.get("/list-tables")
async def list_tables():
    """
    List all tables in ksqlDB.
    
    Returns:
        JSON response with list of tables
    """
    try:
        tables = ksqldb_handler.list_tables()
        return JSONResponse({
            "success": True,
            "tables": tables,
            "count": len(tables)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tables: {str(e)}"
        )


@router.get("/list-connectors")
async def list_connectors():
    """
    List all connectors in ksqlDB.
    
    Returns:
        JSON response with list of connectors
    """
    try:
        connectors = ksqldb_handler.list_connectors()
        return JSONResponse({
            "success": True,
            "connectors": connectors,
            "count": len(connectors)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing connectors: {str(e)}"
        )


@router.get("/list-topics")
async def list_topics():
    """
    List all topics in ksqlDB.
    
    Returns:
        JSON response with list of topics
    """
    try:
        topics = ksqldb_handler.list_topics()
        return JSONResponse({
            "success": True,
            "topics": topics,
            "count": len(topics)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing topics: {str(e)}"
        )


@router.get("/describe-stream/{stream_name}")
async def describe_stream(stream_name: str):
    """
    Get detailed information about a stream.
    
    Args:
        stream_name: Name of the stream to describe
    
    Returns:
        JSON response with stream description
    """
    try:
        description = ksqldb_handler.describe_stream(stream_name)
        if description:
            return JSONResponse({
                "success": True,
                "stream_name": stream_name,
                "description": description
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Stream '{stream_name}' not found or could not be described"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error describing stream: {str(e)}"
        )


@router.get("/describe-table/{table_name}")
async def describe_table(table_name: str):
    """
    Get detailed information about a table.
    
    Args:
        table_name: Name of the table to describe
    
    Returns:
        JSON response with table description
    """
    try:
        description = ksqldb_handler.describe_table(table_name)
        if description:
            return JSONResponse({
                "success": True,
                "table_name": table_name,
                "description": description
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found or could not be described"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error describing table: {str(e)}"
        )


@router.delete("/drop-stream/{stream_name}")
async def drop_stream(stream_name: str, delete_topic: bool = False):
    """
    Drop a stream from ksqlDB.
    
    Args:
        stream_name: Name of the stream to drop
        delete_topic: Whether to delete the underlying topic
    
    Returns:
        JSON response with drop operation status
    """
    try:
        success = ksqldb_handler.drop_stream(stream_name, delete_topic)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Stream '{stream_name}' dropped successfully",
                "stream_name": stream_name,
                "delete_topic": delete_topic
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to drop stream '{stream_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error dropping stream: {str(e)}"
        )


@router.delete("/drop-table/{table_name}")
async def drop_table(table_name: str, delete_topic: bool = False):
    """
    Drop a table from ksqlDB.
    
    Args:
        table_name: Name of the table to drop
        delete_topic: Whether to delete the underlying topic
    
    Returns:
        JSON response with drop operation status
    """
    try:
        success = ksqldb_handler.drop_table(table_name, delete_topic)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Table '{table_name}' dropped successfully",
                "table_name": table_name,
                "delete_topic": delete_topic
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to drop table '{table_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error dropping table: {str(e)}"
        )


@router.delete("/drop-connector/{connector_name}")
async def drop_connector(connector_name: str):
    """
    Drop a connector from ksqlDB.
    
    Args:
        connector_name: Name of the connector to drop
    
    Returns:
        JSON response with drop operation status
    """
    try:
        success = ksqldb_handler.drop_connector(connector_name)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Connector '{connector_name}' dropped successfully",
                "connector_name": connector_name
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to drop connector '{connector_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error dropping connector: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Perform a health check on the ksqlDB server.
    
    Returns:
        JSON response with health status
    """
    try:
        is_healthy = ksqldb_handler.health_check()
        server_info = ksqldb_handler.get_server_info()
        
        return JSONResponse({
            "success": True,
            "healthy": is_healthy,
            "server_info": server_info
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during health check: {str(e)}"
        )


# Utility functions for common operations
def create_user_activity_stream(user_id: str, activity_data: Dict[str, Any]) -> bool:
    """
    Create a user activity stream and insert data.
    
    Args:
        user_id: User identifier
        activity_data: Activity data to insert
        
    Returns:
        bool: True if operation was successful
    """
    try:
        # Create stream if it doesn't exist
        stream_name = f"user_activity_{user_id}"
        stream_config = f"""
        CREATE STREAM {stream_name} (
            user_id VARCHAR,
            activity_type VARCHAR,
            timestamp BIGINT,
            metadata MAP<VARCHAR, VARCHAR>
        ) WITH (
            kafka_topic='user_activity_{user_id}',
            value_format='JSON'
        );
        """
        
        success = ksqldb_handler.create_stream(stream_name, stream_config)
        if success:
            # Insert the activity data
            return ksqldb_handler.insert_data(stream_name, activity_data)
        return False
        
    except Exception as e:
        logger.error(f"Error creating user activity stream: {e}")
        return False


def create_event_stream(stream_name: str, event_data: Dict[str, Any]) -> bool:
    """
    Create an event stream and insert data.
    
    Args:
        stream_name: Name of the event stream
        event_data: Event data to insert
        
    Returns:
        bool: True if operation was successful
    """
    try:
        # Create stream if it doesn't exist
        stream_config = f"""
        CREATE STREAM {stream_name} (
            event_id VARCHAR,
            event_type VARCHAR,
            timestamp BIGINT,
            payload MAP<VARCHAR, VARCHAR>
        ) WITH (
            kafka_topic='{stream_name}',
            value_format='JSON'
        );
        """
        
        success = ksqldb_handler.create_stream(stream_name, stream_config)
        if success:
            # Insert the event data
            return ksqldb_handler.insert_data(stream_name, event_data)
        return False
        
    except Exception as e:
        logger.error(f"Error creating event stream: {e}")
        return False 
