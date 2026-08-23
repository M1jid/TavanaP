"""
Example usage of the ElasticHandler class.
"""

from elastic_handler import ElasticHandler
from elastic_config import get_elastic_config, get_index_name
import time
from datetime import datetime


def example_usage():
    """Example of how to use the ElasticHandler class."""
    
    # Initialize Elasticsearch handler with configuration
    config = get_elastic_config()
    elastic_handler = ElasticHandler(**config)
    
    # Example 1: Health check
    print("=== Health Check ===")
    is_healthy = elastic_handler.health_check()
    if is_healthy:
        print("Elasticsearch cluster is healthy!")
        cluster_info = elastic_handler.get_cluster_info()
        print(f"Cluster info: {cluster_info}")
    else:
        print("Elasticsearch cluster is not healthy!")
        return
    
    # Example 2: Create an index
    print("\n=== Creating Index ===")
    index_name = "users"
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
                "age": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    }
    
    success = elastic_handler.create_index(index_name, index_config)
    if success:
        print(f"Index '{index_name}' created successfully!")
    else:
        print(f"Failed to create index '{index_name}'")
    
    # Example 3: Index a document
    print("\n=== Indexing Document ===")
    user_data = {
        "user_id": "user123",
        "username": "john_doe",
        "email": "john@example.com",
        "age": 30,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    document_id = elastic_handler.index_document(index_name, user_data)
    if document_id:
        print(f"Document indexed successfully with ID: {document_id}")
        print(f"Data: {user_data}")
    else:
        print(f"Failed to index document in index '{index_name}'")
    
    # Example 4: Bulk index documents
    print("\n=== Bulk Indexing Documents ===")
    users_data = [
        {
            "user_id": "user124",
            "username": "jane_smith",
            "email": "jane@example.com",
            "age": 25,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "user_id": "user125",
            "username": "bob_wilson",
            "email": "bob@example.com",
            "age": 35,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    result = elastic_handler.bulk_index(index_name, users_data)
    print(f"Bulk indexing result: {result}")
    
    # Example 5: Search documents
    print("\n=== Searching Documents ===")
    search_query = {
        "query": {
            "match": {
                "username": "john"
            }
        }
    }
    
    search_results = elastic_handler.search_documents(index_name, search_query)
    if search_results:
        total_hits = search_results.get('hits', {}).get('total', {}).get('value', 0)
        hits = search_results.get('hits', {}).get('hits', [])
        print(f"Search returned {total_hits} hits:")
        for hit in hits:
            print(f"  - {hit['_source']}")
    else:
        print("Search failed")
    
    # Example 6: Get document by ID
    print("\n=== Getting Document by ID ===")
    if document_id:
        document = elastic_handler.get_document_by_id(index_name, document_id)
        if document:
            print(f"Retrieved document: {document}")
        else:
            print(f"Document '{document_id}' not found")
    
    # Example 7: Update document
    print("\n=== Updating Document ===")
    if document_id:
        update_data = {
            "age": 31,
            "updated_at": datetime.now().isoformat()
        }
        
        success = elastic_handler.update_document(index_name, document_id, update_data)
        if success:
            print(f"Document '{document_id}' updated successfully")
        else:
            print(f"Failed to update document '{document_id}'")
    
    # Example 8: List all indices
    print("\n=== Listing Indices ===")
    indices = elastic_handler.list_indices()
    print(f"Found {len(indices)} indices: {indices}")
    
    # Example 9: Get index count
    print("\n=== Getting Index Count ===")
    count = elastic_handler.get_index_count(index_name)
    if count is not None:
        print(f"Index '{index_name}' has {count} documents")
    else:
        print(f"Failed to get count for index '{index_name}'")
    
    # Example 10: Get index status
    print("\n=== Getting Index Status ===")
    status = elastic_handler.get_index_status(index_name)
    if status:
        print(f"Index '{index_name}' status: {status}")
    else:
        print(f"Failed to get status for index '{index_name}'")


def example_with_error_handling():
    """Example with proper error handling."""
    
    try:
        # Initialize Elasticsearch handler
        config = get_elastic_config()
        elastic_handler = ElasticHandler(**config)
        
        # Health check
        if not elastic_handler.health_check():
            return {
                "success": False,
                "message": "Elasticsearch cluster is not healthy"
            }
        
        # Create a simple index
        index_name = "test_index"
        index_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "message": {"type": "text"},
                    "timestamp": {"type": "date"}
                }
            }
        }
        
        success = elastic_handler.create_index(index_name, index_config)
        
        if success:
            # Index test document
            test_data = {
                "id": "test123",
                "message": "Hello Elasticsearch!",
                "timestamp": datetime.now().isoformat()
            }
            
            document_id = elastic_handler.index_document(index_name, test_data)
            
            if document_id:
                return {
                    "success": True,
                    "message": "Index created and document indexed successfully",
                    "index_name": index_name,
                    "document_id": document_id,
                    "data": test_data
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to index document"
                }
        else:
            return {
                "success": False,
                "message": "Failed to create index"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def example_logging_system():
    """Example of implementing a logging system with Elasticsearch."""
    
    try:
        config = get_elastic_config()
        elastic_handler = ElasticHandler(**config)
        
        # Create logs index
        logs_index = "application_logs"
        logs_config = {
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
                    "user_id": {"type": "keyword"},
                    "ip_address": {"type": "ip"},
                    "user_agent": {"type": "text"}
                }
            }
        }
        
        elastic_handler.ensure_index_exists(logs_index, logs_config)
        
        # Index some sample logs
        sample_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "User login successful",
                "service": "auth-service",
                "user_id": "user123",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Database connection failed",
                "service": "db-service",
                "user_id": None,
                "ip_address": "192.168.1.2",
                "user_agent": "Python/3.8"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "WARN",
                "message": "High memory usage detected",
                "service": "monitoring-service",
                "user_id": None,
                "ip_address": "192.168.1.3",
                "user_agent": "Monitoring Agent"
            }
        ]
        
        result = elastic_handler.bulk_index(logs_index, sample_logs)
        print(f"Indexed {result.get('success_count', 0)} log entries")
        
        # Search for error logs
        error_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"level": "ERROR"}},
                        {"range": {"timestamp": {"gte": "now-1h"}}}
                    ]
                }
            },
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        error_results = elastic_handler.search_documents(logs_index, error_query, size=10)
        if error_results:
            total_hits = error_results.get('hits', {}).get('total', {}).get('value', 0)
            print(f"Found {total_hits} error logs in the last hour")
        
        return {
            "success": True,
            "message": "Logging system example completed",
            "indexed_logs": result.get('success_count', 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in logging system: {str(e)}"
        }


def example_user_management():
    """Example of user management with Elasticsearch."""
    
    try:
        config = get_elastic_config()
        elastic_handler = ElasticHandler(**config)
        
        # Create users index
        users_index = "users"
        users_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "username": {"type": "text"},
                    "email": {"type": "keyword"},
                    "first_name": {"type": "text"},
                    "last_name": {"type": "text"},
                    "age": {"type": "integer"},
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        elastic_handler.ensure_index_exists(users_index, users_config)
        
        # Index sample users
        sample_users = [
            {
                "user_id": "user001",
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "age": 30,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "user_id": "user002",
                "username": "jane_smith",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "age": 25,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "user_id": "user003",
                "username": "bob_wilson",
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Wilson",
                "age": 35,
                "is_active": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        result = elastic_handler.bulk_index(users_index, sample_users)
        print(f"Indexed {result.get('success_count', 0)} users")
        
        # Search for active users
        active_users_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"is_active": True}},
                        {"range": {"age": {"gte": 18, "lte": 65}}}
                    ]
                }
            },
            "sort": [{"created_at": {"order": "desc"}}]
        }
        
        active_results = elastic_handler.search_documents(users_index, active_users_query, size=10)
        if active_results:
            total_hits = active_results.get('hits', {}).get('total', {}).get('value', 0)
            print(f"Found {total_hits} active users between 18-65 years old")
        
        # Search by name
        name_search_query = {
            "query": {
                "multi_match": {
                    "query": "john",
                    "fields": ["first_name", "last_name", "username"],
                    "type": "best_fields"
                }
            }
        }
        
        name_results = elastic_handler.search_documents(users_index, name_search_query, size=5)
        if name_results:
            hits = name_results.get('hits', {}).get('hits', [])
            print(f"Found {len(hits)} users matching 'john'")
        
        return {
            "success": True,
            "message": "User management example completed",
            "indexed_users": result.get('success_count', 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in user management: {str(e)}"
        }


def example_index_management():
    """Example of index management operations."""
    
    try:
        config = get_elastic_config()
        elastic_handler = ElasticHandler(**config)
        
        # List existing indices
        print("Existing indices:")
        indices = elastic_handler.list_indices()
        print(indices)
        
        # Create a test index
        test_index = "test_management"
        test_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "data": {"type": "text"}
                }
            }
        }
        
        success = elastic_handler.create_index(test_index, test_config)
        if success:
            print(f"Created index '{test_index}'")
            
            # Index some data
            test_data = {
                "id": "test1",
                "data": "Sample data for testing"
            }
            
            doc_id = elastic_handler.index_document(test_index, test_data)
            if doc_id:
                print(f"Indexed document with ID: {doc_id}")
                
                # Refresh index to make changes visible
                elastic_handler.refresh_index(test_index)
                print(f"Refreshed index '{test_index}'")
                
                # Get index count
                count = elastic_handler.get_index_count(test_index)
                print(f"Index '{test_index}' has {count} documents")
                
                # Get index status
                status = elastic_handler.get_index_status(test_index)
                print(f"Index '{test_index}' status retrieved")
                
                # Flush index
                elastic_handler.flush_index(test_index)
                print(f"Flushed index '{test_index}'")
                
                # Delete the test index
                delete_success = elastic_handler.delete_index(test_index)
                if delete_success:
                    print(f"Deleted index '{test_index}'")
                else:
                    print(f"Failed to delete index '{test_index}'")
            else:
                print("Failed to index test document")
        else:
            print(f"Failed to create index '{test_index}'")
        
        return {
            "success": True,
            "message": "Index management example completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in index management: {str(e)}"
        }


if __name__ == "__main__":
    print("Elasticsearch Handler Example Usage")
    print("=" * 40)
    
    # Run basic examples
    example_usage()
    
    print("\n" + "=" * 40)
    print("Error Handling Example")
    print("=" * 40)
    result = example_with_error_handling()
    print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("Logging System Example")
    print("=" * 40)
    result = example_logging_system()
    print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("User Management Example")
    print("=" * 40)
    result = example_user_management()
    print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("Index Management Example")
    print("=" * 40)
    result = example_index_management()
    print(f"Result: {result}") 