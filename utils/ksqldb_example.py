"""
Example usage of the KsqlDBHandler class.
"""

from ksqldb_handler import KsqlDBHandler
from ksqldb_config import get_ksqldb_config
import time
from datetime import datetime


def example_usage():
    """Example of how to use the KsqlDBHandler class."""
    
    # Initialize ksqlDB handler with configuration
    config = get_ksqldb_config()
    ksqldb_handler = KsqlDBHandler(**config)
    
    # Example 1: Health check
    print("=== Health Check ===")
    is_healthy = ksqldb_handler.health_check()
    if is_healthy:
        print("ksqlDB server is healthy!")
        server_info = ksqldb_handler.get_server_info()
        print(f"Server info: {server_info}")
    else:
        print("ksqlDB server is not healthy!")
        return
    
    # Example 2: Create a stream
    print("\n=== Creating Stream ===")
    stream_name = "user_events"
    stream_config = """
    CREATE STREAM user_events (
        user_id VARCHAR,
        event_type VARCHAR,
        timestamp BIGINT,
        metadata MAP<VARCHAR, VARCHAR>
    ) WITH (
        kafka_topic='user_events',
        value_format='JSON'
    );
    """
    
    success = ksqldb_handler.create_stream(stream_name, stream_config)
    if success:
        print(f"Stream '{stream_name}' created successfully!")
    else:
        print(f"Failed to create stream '{stream_name}'")
    
    # Example 3: Insert data into stream
    print("\n=== Inserting Data ===")
    event_data = {
        "user_id": "user123",
        "event_type": "login",
        "timestamp": int(time.time() * 1000),
        "metadata": {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }
    }
    
    success = ksqldb_handler.insert_data(stream_name, event_data)
    if success:
        print(f"Data inserted successfully into stream '{stream_name}'")
        print(f"Data: {event_data}")
    else:
        print(f"Failed to insert data into stream '{stream_name}'")
    
    # Example 4: Create a table
    print("\n=== Creating Table ===")
    table_name = "user_profiles"
    table_config = """
    CREATE TABLE user_profiles (
        user_id VARCHAR PRIMARY KEY,
        username VARCHAR,
        email VARCHAR,
        created_at BIGINT
    ) WITH (
        kafka_topic='user_profiles',
        value_format='JSON'
    );
    """
    
    success = ksqldb_handler.create_table(table_name, table_config)
    if success:
        print(f"Table '{table_name}' created successfully!")
    else:
        print(f"Failed to create table '{table_name}'")
    
    # Example 5: Create a sink connector
    print("\n=== Creating Sink Connector ===")
    connector_name = "elasticsearch_sink"
    connector_config = """
    CREATE SINK CONNECTOR elasticsearch_sink WITH (
        'connector.class' = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
        'topics' = 'user_events',
        'connection.url' = 'http://elasticsearch:9200',
        'type.name' = 'user_event',
        'key.ignore' = 'true',
        'schema.ignore' = 'true'
    );
    """
    
    success = ksqldb_handler.create_sink_connector(connector_name, connector_config)
    if success:
        print(f"Connector '{connector_name}' created successfully!")
    else:
        print(f"Failed to create connector '{connector_name}'")
    
    # Example 6: List all streams, tables, and connectors
    print("\n=== Listing Objects ===")
    streams = ksqldb_handler.list_streams()
    print(f"Streams: {streams}")
    
    tables = ksqldb_handler.list_tables()
    print(f"Tables: {tables}")
    
    connectors = ksqldb_handler.list_connectors()
    print(f"Connectors: {connectors}")
    
    topics = ksqldb_handler.list_topics()
    print(f"Topics: {topics}")
    
    # Example 7: Describe a stream
    print("\n=== Describing Stream ===")
    description = ksqldb_handler.describe_stream(stream_name)
    if description:
        print(f"Stream '{stream_name}' description:")
        print(description)
    else:
        print(f"Could not describe stream '{stream_name}'")
    
    # Example 8: Execute a custom query
    print("\n=== Executing Custom Query ===")
    custom_query = "SELECT user_id, event_type, timestamp FROM user_events EMIT CHANGES LIMIT 5;"
    result = ksqldb_handler.execute_query(custom_query)
    if result:
        print(f"Query result: {result}")
    else:
        print("Failed to execute custom query")


def example_with_error_handling():
    """Example with proper error handling."""
    
    try:
        # Initialize ksqlDB handler
        config = get_ksqldb_config()
        ksqldb_handler = KsqlDBHandler(**config)
        
        # Health check
        if not ksqldb_handler.health_check():
            return {
                "success": False,
                "message": "ksqlDB server is not healthy"
            }
        
        # Create a simple stream
        stream_name = "test_stream"
        stream_config = """
        CREATE STREAM test_stream (
            id VARCHAR,
            message VARCHAR,
            timestamp BIGINT
        ) WITH (
            kafka_topic='test_stream',
            value_format='JSON'
        );
        """
        
        success = ksqldb_handler.create_stream(stream_name, stream_config)
        
        if success:
            # Insert test data
            test_data = {
                "id": "test123",
                "message": "Hello ksqlDB!",
                "timestamp": int(time.time() * 1000)
            }
            
            insert_success = ksqldb_handler.insert_data(stream_name, test_data)
            
            if insert_success:
                return {
                    "success": True,
                    "message": "Stream created and data inserted successfully",
                    "stream_name": stream_name,
                    "data": test_data
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to insert data into stream"
                }
        else:
            return {
                "success": False,
                "message": "Failed to create stream"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def example_stream_processing():
    """Example of stream processing with ksqlDB."""
    
    try:
        config = get_ksqldb_config()
        ksqldb_handler = KsqlDBHandler(**config)
        
        # Create source stream for orders
        orders_stream = "orders"
        orders_config = """
        CREATE STREAM orders (
            order_id VARCHAR,
            user_id VARCHAR,
            product_id VARCHAR,
            quantity INT,
            price DOUBLE,
            timestamp BIGINT
        ) WITH (
            kafka_topic='orders',
            value_format='JSON'
        );
        """
        
        ksqldb_handler.create_stream(orders_stream, orders_config)
        
        # Create a table to track user order counts
        user_orders_table = "user_order_counts"
        user_orders_config = """
        CREATE TABLE user_order_counts AS
        SELECT user_id,
               COUNT(*) as order_count,
               SUM(quantity * price) as total_spent
        FROM orders
        GROUP BY user_id
        EMIT CHANGES;
        """
        
        ksqldb_handler.execute_query(user_orders_config)
        
        # Insert some sample orders
        sample_orders = [
            {
                "order_id": "order1",
                "user_id": "user1",
                "product_id": "prod1",
                "quantity": 2,
                "price": 29.99,
                "timestamp": int(time.time() * 1000)
            },
            {
                "order_id": "order2",
                "user_id": "user1",
                "product_id": "prod2",
                "quantity": 1,
                "price": 49.99,
                "timestamp": int(time.time() * 1000)
            },
            {
                "order_id": "order3",
                "user_id": "user2",
                "product_id": "prod1",
                "quantity": 3,
                "price": 29.99,
                "timestamp": int(time.time() * 1000)
            }
        ]
        
        for order in sample_orders:
            ksqldb_handler.insert_data(orders_stream, order)
            print(f"Inserted order: {order['order_id']}")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Query the aggregated results
        query = "SELECT * FROM user_order_counts EMIT CHANGES LIMIT 10;"
        result = ksqldb_handler.execute_query(query)
        
        print("User order counts:")
        print(result)
        
        return {
            "success": True,
            "message": "Stream processing example completed",
            "results": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in stream processing: {str(e)}"
        }


def example_connector_management():
    """Example of managing connectors with ksqlDB."""
    
    try:
        config = get_ksqldb_config()
        ksqldb_handler = KsqlDBHandler(**config)
        
        # List existing connectors
        print("Existing connectors:")
        connectors = ksqldb_handler.list_connectors()
        print(connectors)
        
        # Create a file sink connector
        connector_name = "file_sink_connector"
        connector_config = """
        CREATE SINK CONNECTOR file_sink_connector WITH (
            'connector.class' = 'org.apache.kafka.connect.file.FileStreamSinkConnector',
            'topics' = 'user_events',
            'file' = '/tmp/user_events.txt',
            'key.converter' = 'org.apache.kafka.connect.storage.StringConverter',
            'value.converter' = 'org.apache.kafka.connect.storage.StringConverter'
        );
        """
        
        success = ksqldb_handler.create_sink_connector(connector_name, connector_config)
        if success:
            print(f"Connector '{connector_name}' created successfully!")
            
            # Wait a moment and check connector status
            time.sleep(2)
            connectors = ksqldb_handler.list_connectors()
            print(f"Updated connectors: {connectors}")
            
            # Drop the connector
            drop_success = ksqldb_handler.drop_connector(connector_name)
            if drop_success:
                print(f"Connector '{connector_name}' dropped successfully!")
            else:
                print(f"Failed to drop connector '{connector_name}'")
        else:
            print(f"Failed to create connector '{connector_name}'")
        
        return {
            "success": True,
            "message": "Connector management example completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in connector management: {str(e)}"
        }


if __name__ == "__main__":
    print("ksqlDB Handler Example Usage")
    print("=" * 40)
    
    # Run basic examples
    example_usage()
    
    print("\n" + "=" * 40)
    print("Error Handling Example")
    print("=" * 40)
    result = example_with_error_handling()
    print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("Stream Processing Example")
    print("=" * 40)
    result = example_stream_processing()
    print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("Connector Management Example")
    print("=" * 40)
    result = example_connector_management()
    print(f"Result: {result}") 
