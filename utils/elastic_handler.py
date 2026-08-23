import requests
import logging
from typing import Optional, Dict, List, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import elasticsearch
from elasticsearch import AsyncElasticsearch
from elastic_transport import ConnectionError, ConnectionTimeout
import json
import asyncio
logger = logging.getLogger(__name__)


class ElasticHandler:
    """
    Elasticsearch handler class using elasticsearch-py to manage Elasticsearch operations.
    
    This class provides methods to:
    - Create and manage indices
    - Index and search documents
    - Manage cluster health and status
    - Query documents by various criteria
    - Bulk operations
    - Monitor Elasticsearch status
    """
    
    def __init__(
        self,
        hosts: Union[str, List[str]],
        username: str,
        password: str,
        max_retries: int = 5,
        retry_on_timeout: bool = True,
        verify_certs: bool = False,
        ssl_show_warn: bool = False
    ):
        """
        Initialize Elasticsearch handler with connection parameters.
        
        Args:
            hosts: Elasticsearch host(s) - can be string or list of strings
            username: Elasticsearch username
            password: Elasticsearch password
            max_retries: Maximum number of retry attempts (default: 5)
            verify_certs: Whether to verify SSL certificates (default: False)
            ssl_show_warn: Whether to show SSL warnings (default: False)
        """
        if isinstance(hosts, str):
            hosts = [hosts]
        
        self.hosts = hosts
        self.username = username
        self.password = password
        self.max_retries = max_retries
        
        # Initialize Elasticsearch client
        self.client = AsyncElasticsearch(
            hosts=hosts,
            http_auth=(username, password),
            max_retries=max_retries,
            retry_on_timeout=True,
            verify_certs=verify_certs,
            ssl_show_warn=ssl_show_warn
        )
    
    async def _test_connection(self) -> bool:
        """
        Test the connection to Elasticsearch cluster.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            info = await self.client.info()
            logger.info(f"Successfully connected to Elasticsearch cluster: {info.get('cluster_name', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, ConnectionTimeout)),
        reraise=True
    )
    async def execute_operation(self, operation_func, *args, **kwargs):
        """
        Execute an Elasticsearch operation with retry mechanism.
        
        Args:
            operation_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation or None if failed
        """
        try:
            result = await operation_func(*args, **kwargs)
            logger.info(f"Operation executed successfully")
            return result
        except (elasticsearch.ConnectionError, elasticsearch.ConnectionTimeout) as e:
            logger.error(f"Elasticsearch operation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Elasticsearch operation: {e}")
            return None
    
    async def create_index(
        self,
        index_name: str,
        body: Dict[str, Any],
        check_exists: bool = True
    ) -> bool:
        """
        Create an index with specific mappings.
        
        Args:
            index_name: Name of the index to create
            body: Index configuration and mappings
            check_exists: Whether to check if index already exists
            
        Returns:
            bool: True if index was created successfully or already exists
        """
        try:
            if check_exists and self.index_exists(index_name):
                logger.info(f"Index '{index_name}' already exists. Skipping creation.")
                return True
            
            response = await self.execute_operation(
                self.client.indices.create,
                index=index_name,
                body=body
            )
            
            if response and response.get('acknowledged'):
                logger.info(f"Successfully created index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to create index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error creating index '{index_name}': {e}")
            return False
    
    async def delete_index(self, index_name: str) -> bool:
        """
        Delete an index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            bool: True if index was deleted successfully
        """
        try:
            if not self.index_exists(index_name):
                logger.info(f"Index '{index_name}' does not exist. Nothing to delete.")
                return True
            
            response = await self.execute_operation(
                self.client.indices.delete,
                index=index_name
            )
            
            if response and response.get('acknowledged'):
                logger.info(f"Successfully deleted index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to delete index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting index '{index_name}': {e}")
            return False
    
    async def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index to check
            
        Returns:
            bool: True if index exists
        """
        try:
            exists = await self.execute_operation(
                self.client.indices.exists,
                index=index_name
            )
            logger.info(f"Index '{index_name}' exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking if index '{index_name}' exists: {e}")
            return False
    
    async def ensure_index_exists(
        self,
        index_name: str,
        index_config: Dict[str, Any]
    ) -> bool:
        """
        Check if index exists, if not create it.
        
        Args:
            index_name: Name of the index
            index_config: Index configuration
            
        Returns:
            bool: True if index exists or was created successfully
        """
        try:
            if self.index_exists(index_name):
                logger.info(f"Index '{index_name}' already exists")
                return True
            else:
                logger.info(f"Index '{index_name}' doesn't exist, creating it")
                return await self.create_index(index_name, index_config, check_exists=False)
                
        except Exception as e:
            logger.error(f"Error ensuring index '{index_name}' exists: {e}")
            return False
    
    async def index_document(
        self,
        index_name: str,
        document: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Index a document.
        
        Args:
            index_name: Name of the index
            document: Document to index
            document_id: Optional document ID
            
        Returns:
            str: Document ID if successful, None otherwise
        """
        try:
            kwargs = {
                'index': index_name,
                'body': document
            }
            if document_id:
                kwargs['id'] = document_id
            
            response = await self.execute_operation(
                self.client.index,
                **kwargs
            )
            
            if response and response.get('result') in ['created', 'updated']:
                doc_id = response.get('_id')
                logger.info(f"Successfully indexed document '{doc_id}' in index '{index_name}'")
                return doc_id
            else:
                logger.error(f"Failed to index document in index '{index_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error indexing document in index '{index_name}': {e}")
            return None
    
    async def bulk_index(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Bulk index multiple documents.
        
        Args:
            index_name: Name of the index
            documents: List of documents to index
            document_ids: Optional list of document IDs
            
        Returns:
            Dict: Summary of bulk operation results
        """
        try:
            actions = []
            for i, doc in enumerate(documents):
                action = {
                    '_index': index_name,
                    '_source': doc
                }
                if document_ids and i < len(document_ids):
                    action['_id'] = document_ids[i]
                actions.append(action)
            
            from elasticsearch.helpers import bulk
            success_count, errors = await bulk(self.client, actions, raise_on_error=False)
            
            logger.info(f"Bulk indexed {success_count} documents in index '{index_name}'")
            if errors:
                logger.warning(f"Bulk indexing had {len(errors)} errors")
            
            return {
                'success_count': success_count,
                'error_count': len(errors),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error bulk indexing documents in index '{index_name}': {e}")
            return {
                'success_count': 0,
                'error_count': len(documents),
                'errors': [str(e)]
            }
    
    async def get_document_by_id(
        self,
        index_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            index_name: Name of the index
            document_id: Document ID
            
        Returns:
            Dict: Document data or None if not found
        """
        try:
            response = await self.execute_operation(
                self.client.get,
                index=index_name,
                id=document_id
            )
            
            if response and response.get('found'):
                logger.info(f"Successfully retrieved document '{document_id}' from index '{index_name}'")
                return response.get('_source')
            else:
                logger.warning(f"Document '{document_id}' not found in index '{index_name}'")
                return None
                
        except elasticsearch.NotFoundError:
            logger.warning(f"Document '{document_id}' not found in index '{index_name}'")
            return None
        except Exception as e:
            logger.error(f"Error getting document '{document_id}' from index '{index_name}': {e}")
            return None
    
    async def search_documents(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Search documents in an index.
        
        Args:
            index_name: Name of the index
            query: Search query
            size: Number of results to return (default: 10)
            from_: Starting offset (default: 0)
            
        Returns:
            Dict: Search results or None if failed
        """
        try:
            response = await self.execute_operation(
                self.client.search,
                index=index_name,
                body=query,
                size=size,
                from_=from_
            )
            
            if response:
                total_hits = response.get('hits', {}).get('total', {}).get('value', 0)
                logger.info(f"Search returned {total_hits} total hits from index '{index_name}'")
                return response
            else:
                logger.error(f"Search failed for index '{index_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error searching documents in index '{index_name}': {e}")
            return None
    
    async def search_scroll(self, index_name: str, size: int = 100, scroll_id: str = None, body: Dict[str, Any] = None, scroll: str = "1m"):
        if scroll_id:
            return await self.execute_operation(
                self.client.scroll,
                scroll_id=scroll_id,
                scroll=scroll,
            )
        else:
            return await self.execute_operation(
                self.client.search,
                index=index_name,
                body=body,
                scroll=scroll,
                size=size,
            )

    async def update_document(
        self,
        index_name: str,
        document_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a document.
        
        Args:
            index_name: Name of the index
            document_id: Document ID
            update_data: Data to update
            
        Returns:
            bool: True if document was updated successfully
        """
        try:
            response = await self.execute_operation(
                self.client.update,
                index=index_name,
                id=document_id,
                body={'doc': update_data}
            )
            
            if response and response.get('result') in ['updated', 'noop']:
                logger.info(f"Successfully updated document '{document_id}' in index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to update document '{document_id}' in index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error updating document '{document_id}' in index '{index_name}': {e}")
            return False
    
    async def delete_document(
        self,
        index_name: str,
        document_id: str
    ) -> bool:
        """
        Delete a document.
        
        Args:
            index_name: Name of the index
            document_id: Document ID
            
        Returns:
            bool: True if document was deleted successfully
        """
        try:
            response = await self.execute_operation(
                self.client.delete,
                index=index_name,
                id=document_id
            )
            
            if response and response.get('result') in ['deleted', 'not_found']:
                logger.info(f"Successfully deleted document '{document_id}' from index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to delete document '{document_id}' from index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document '{document_id}' from index '{index_name}': {e}")
            return False
    
    async def get_index_count(self, index_name: str) -> Optional[int]:
        """
        Get the document count for an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            int: Document count or None if failed
        """
        try:
            response = await self.execute_operation(
                self.client.count,
                index=index_name
            )
            
            if response:
                count = response.get('count', 0)
                logger.info(f"Index '{index_name}' has {count} documents")
                return count
            else:
                logger.error(f"Failed to get count for index '{index_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error getting count for index '{index_name}': {e}")
            return None
    
    async def get_index_status(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status information for an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dict: Index status information or None if failed
        """
        try:
            response = await self.execute_operation(
                self.client.indices.get,
                index=index_name
            )
            
            if response:
                logger.info(f"Successfully retrieved status for index '{index_name}'")
                return response
            else:
                logger.error(f"Failed to get status for index '{index_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error getting status for index '{index_name}': {e}")
            return None
    
    async def list_indices(self) -> List[str]:
        """
        List all indices.
        
        Returns:
            List[str]: List of index names
        """
        try:
            response = await self.execute_operation(
                self.client.indices.get,
                index='*'
            )
            
            if response:
                indices = list(response.keys())
                logger.info(f"Found {len(indices)} indices")
                return indices
            else:
                logger.error("Failed to list indices")
                return []
                
        except Exception as e:
            logger.error(f"Error listing indices: {e}")
            return []
    
    async def get_cluster_health(self) -> Optional[Dict[str, Any]]:
        """
        Get cluster health information.
        
        Returns:
            Dict: Cluster health information or None if failed
        """
        try:
            response = await self.execute_operation(
                self.client.cluster.health
            )
            
            if response:
                status = response.get('status', 'unknown')
                logger.info(f"Cluster health status: {status}")
                return response
            else:
                logger.error("Failed to get cluster health")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cluster health: {e}")
            return None
    
    async def get_cluster_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cluster information.
        
        Returns:
            Dict: Cluster information or None if failed
        """
        try:
            response = await self.execute_operation(
                self.client.info
            )
            
            if response:
                cluster_name = response.get('cluster_name', 'unknown')
                version = response.get('version', {}).get('number', 'unknown')
                logger.info(f"Cluster: {cluster_name}, Version: {version}")
                return response
            else:
                logger.error("Failed to get cluster info")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the Elasticsearch cluster.
        
        Returns:
            bool: True if cluster is healthy
        """
        try:
            health = await self.get_cluster_health()
            if health:
                status = health.get('status', 'unknown')
                return status in ['green', 'yellow']
            else:
                logger.error("Elasticsearch cluster health check failed")
                return False
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return False
    
    async def refresh_index(self, index_name: str) -> bool:
        """
        Refresh an index to make recent changes visible.
        
        Args:
            index_name: Name of the index to refresh
            
        Returns:
            bool: True if index was refreshed successfully
        """
        try:
            response = await self.execute_operation(
                self.client.indices.refresh,
                index=index_name
            )
            
            if response and response.get('_shards', {}).get('failed', 0) == 0:
                logger.info(f"Successfully refreshed index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to refresh index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing index '{index_name}': {e}")
            return False
    
    async def flush_index(self, index_name: str) -> bool:
        """
        Flush an index to persist changes to disk.
        
        Args:
            index_name: Name of the index to flush
            
        Returns:
            bool: True if index was flushed successfully
        """
        try:
            response = await self.execute_operation(
                self.client.indices.flush,
                index=index_name
            )
            
            if response and response.get('_shards', {}).get('failed', 0) == 0:
                logger.info(f"Successfully flushed index '{index_name}'")
                return True
            else:
                logger.error(f"Failed to flush index '{index_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error flushing index '{index_name}': {e}")
            return False 
