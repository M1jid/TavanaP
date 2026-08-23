import requests
import logging
from typing import Optional, Dict, List, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import signal
import json

logger = logging.getLogger(__name__)

HEADERS = {"Content-Type": "application/vnd.ksql.v1+json"}


class KsqlDBHandler:
    """
    ksqlDB handler class using requests to manage ksqlDB operations.
    
    This class provides methods to:
    - Execute ksqlDB queries
    - Create streams and tables
    - Create sink connectors
    - Insert data into streams
    - List streams, tables, and connectors
    - Drop streams, tables, and connectors
    - Monitor ksqlDB status
    """
    
    def __init__(
        self,
        ksqldb_url: str,
        timeout: int = 30,
        max_retries: int = 5
    ):
        """
        Initialize ksqlDB handler with connection parameters.
        
        Args:
            ksqldb_url: ksqlDB server URL (e.g., http://localhost:8088)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 5)
        """
        self.ksqldb_url = ksqldb_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """
        Test the connection to ksqlDB server.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            response = requests.get(f"{self.ksqldb_url.rstrip('ksql')}/info", timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully connected to ksqlDB at {self.ksqldb_url}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to ksqlDB at {self.ksqldb_url}: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def execute_query(self, query: str, stream_properties: Optional[Dict] = None, log: str = None) -> Optional[Dict]:
        """
        Execute a ksqlDB query with retry mechanism.
        
        Args:
            query: ksqlDB query to execute
            stream_properties: Optional stream properties for the query
            
        Returns:
            Dict: Query response or None if failed
        """
        try:
            payload = {
                "ksql": query,
                "streamsProperties": stream_properties or {}
            }
            
            response = requests.post(
                self.ksqldb_url,
                headers=HEADERS,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if log:
                logger.info(f"Query executed successfully: {log}")
                # logger.info(f"Query result: {payload}")
            else:
                logger.info(f"Query executed successfully")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error executing ksqlDB query: {e}")
            logger.error(f"Query: {query}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing ksqlDB query: {e}")
            return None
    
    def create_stream(
        self,
        stream_name: str,
        stream_config: str,
        check_exists: bool = True
    ) -> bool:
        """
        Create a stream in ksqlDB.
        
        Args:
            stream_name: Name of the stream to create
            stream_config: Stream creation configuration/query
            check_exists: Whether to check if stream already exists
            
        Returns:
            bool: True if stream was created successfully or already exists
        """
        try:
            if check_exists:
                # Check if the stream already exists
                existing_streams = self.list_streams()
                if stream_name in existing_streams:
                    logger.info(f"Stream '{stream_name}' already exists. Skipping creation.")
                    return True
            
            # Create the stream
            response = self.execute_query(stream_config)
            if response:
                logger.info(f"Successfully created stream '{stream_name}'")
                return True
            else:
                logger.error(f"Failed to create stream '{stream_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error creating stream '{stream_name}': {e}")
            return False
    
    def create_table(
        self,
        table_name: str,
        table_config: str,
        check_exists: bool = True
    ) -> bool:
        """
        Create a table in ksqlDB.
        
        Args:
            table_name: Name of the table to create
            table_config: Table creation configuration/query
            check_exists: Whether to check if table already exists
            
        Returns:
            bool: True if table was created successfully or already exists
        """
        try:
            if check_exists:
                # Check if the table already exists
                existing_tables = self.list_tables()
                if table_name in existing_tables:
                    logger.info(f"Table '{table_name}' already exists. Skipping creation.")
                    return True
            
            # Create the table
            response = self.execute_query(table_config)
            if response:
                logger.info(f"Successfully created table '{table_name}'")
                return True
            else:
                logger.error(f"Failed to create table '{table_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error creating table '{table_name}': {e}")
            return False
    
    def create_sink_connector(
        self,
        connector_name: str,
        connector_config: str,
        check_exists: bool = True
    ) -> bool:
        """
        Create a sink connector in ksqlDB.
        
        Args:
            connector_name: Name of the connector to create
            connector_config: Connector creation configuration/query
            check_exists: Whether to check if connector already exists
            
        Returns:
            bool: True if connector was created successfully or already exists
        """
        try:
            if check_exists:
                # Check if the connector already exists
                existing_connectors = self.list_connectors()
                if connector_name in existing_connectors:
                    logger.info(f"Connector '{connector_name}' already exists. Skipping creation.")
                    return True
            
            # Create the connector
            response = self.execute_query(connector_config)
            if response:
                logger.info(f"Successfully created connector '{connector_name}'")
                return True
            else:
                logger.error(f"Failed to create connector '{connector_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error creating connector '{connector_name}': {e}")
            return False
    
    def delete_sink_connector(self, connector_name: str, check_exists: bool = True) -> bool:
        """
        Delete a sink connector from ksqlDB.
        
        Args:
            connector_name: Name of the connector to delete
            check_exists: Whether to check if connector already exists
        """
        try:
            if check_exists:
                # Check if the connector already exists
                existing_connectors = self.list_connectors()
                if connector_name not in existing_connectors:
                    logger.info(f"Connector '{connector_name}' does not exist. Skipping deletion.")
                    return True
            
            query = f"DROP CONNECTOR {connector_name};"
            response = self.execute_query(query)
            if response:
                logger.info(f"Successfully deleted connector '{connector_name}'")
                return True
            else:
                logger.error(f"Failed to delete connector '{connector_name}'")
                return False
        except Exception as e:
            logger.error(f"Error deleting connector '{connector_name}': {e}")
            return False

    def insert_data(self, stream_name: str, data: Dict[str, Any]) -> bool:
        """
        Insert data into a ksqlDB stream.
        
        Args:
            stream_name: Name of the stream to insert data into
            data: Dictionary containing the data to insert
            
        Returns:
            bool: True if data was inserted successfully
        """
        try:
            # Build the INSERT query
            values = self._build_values_string(data)
            keys = ", ".join([f"{k}" if isinstance(k, str) else str(k) for k in data.keys()])
            query = f"INSERT INTO {stream_name} ({keys}) VALUES ({values});"
            self.execute_query(query, log=data['ID'] if 'ID' in data else data['LINK'] if 'LINK' in data else data['URL'] if 'URL' in data else None)
        except Exception as e:
            logger.error(f"Error inserting data into stream '{stream_name}': {e}")
            logger.error(f"Query: {query}")
            return False
    
    def _build_values_string(self, data: Dict[str, Any]) -> str:
        def _escape_str(s: str) -> str:
            # SQL single-quote escaping: ' -> ''
            return s.replace("'", "''")

        def _ksql_literal(v: Any, in_array: bool = False) -> str:
            if v is None:
                return "NULL"
            if isinstance(v, bool):
                return "TRUE" if v else "FALSE"
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, str):
                return f"'{_escape_str(v)}'"
            if isinstance(v, list):
                if not v:
                    return "NULL"
                return "ARRAY[" + ", ".join(_ksql_literal(item, in_array=True) for item in v) + "]"
            if isinstance(v, dict):
                if in_array:
                    # Treat dicts inside arrays as STRUCTs for ARRAY<STRUCT<...>>
                    fields = [f"{str(k).upper()} := {_ksql_literal(val)}" for k, val in v.items()]
                    return "STRUCT(" + ", ".join(fields) + ")"
                # Top-level dicts are MAPs
                if not v:
                    return "NULL"
                entries = [f"'{k}':= {_ksql_literal(val)}" for k, val in v.items()]
                return "MAP(" + ", ".join(entries) + ")"
            # Fallback: stringify and quote
            return f"'{_escape_str(str(v))}'"

        values = ''
        for val in data.values():
            values += ", " + _ksql_literal(val)

        return values[2:] if values.startswith(", ") else values

    # def _build_values_string(self, data: Dict[str, Any]) -> str:
    #     """
    #     Build the VALUES string for INSERT queries.
        
    #     Args:
    #         data: Dictionary containing the data
            
    #     Returns:
    #         str: Formatted VALUES string
    #     """
    #     values = ''
    #     for val in data.values():
    #         if isinstance(val, int):
    #             values += f', {str(val)}'
    #         elif isinstance(val, str):
    #             values += f", '{val}'"
    #         elif isinstance(val, dict):
    #             if len(list(val.keys())) == 0:
    #                 values += ", NULL"
    #             else:
    #                 values += ', MAP ('
    #                 metadata = ''
    #                 for key_dict, value_dict in val.items():
    #                     metadata += f",'{key_dict}':={str(value_dict)}"
    #                 metadata = metadata[1:]
    #                 values += f'{metadata})'
    #         elif isinstance(val, list):
    #             if len(val) == 0:
    #                 values += ", NULL"
    #             else:
    #                 values += ', ARRAY['
    #                 metadata = ''
    #                 for item in val:
    #                     metadata += f", '{item}'"
    #                 metadata = metadata[1:]
    #                 values += f'{metadata}]'
    #         elif val is None:
    #             values += ", NULL"
    #         else:
    #             values += f", {str(val)}"
        
    #     return values[1:] if values.startswith(', ') else values
    
    def list_streams(self) -> List[str]:
        """
        List all streams in ksqlDB.
        
        Returns:
            List[str]: List of stream names
        """
        try:
            response = self.execute_query("SHOW STREAMS;")
            if response and len(response) > 0:
                streams = [stream['name'] for stream in response[0].get('streams', [])]
                logger.info(f"Found {len(streams)} streams")
                return streams
            return []
        except Exception as e:
            logger.error(f"Error listing streams: {e}")
            return []
    
    def list_tables(self) -> List[str]:
        """
        List all tables in ksqlDB.
        
        Returns:
            List[str]: List of table names
        """
        try:
            response = self.execute_query("SHOW TABLES;")
            if response and len(response) > 0:
                tables = [table['name'] for table in response[0].get('tables', [])]
                logger.info(f"Found {len(tables)} tables")
                return tables
            return []
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def list_connectors(self) -> List[str]:
        """
        List all connectors in ksqlDB.
        
        Returns:
            List[str]: List of connector names
        """
        try:
            response = self.execute_query("SHOW CONNECTORS;")
            if response and len(response) > 0:
                connectors = [connector['name'] for connector in response[0].get('connectors', [])]
                logger.info(f"Found {len(connectors)} connectors")
                return connectors
            return []
        except Exception as e:
            logger.error(f"Error listing connectors: {e}")
            return []
    
    def list_topics(self) -> List[str]:
        """
        List all topics in ksqlDB.
        
        Returns:
            List[str]: List of topic names
        """
        try:
            response = self.execute_query("SHOW TOPICS;")
            if response and len(response) > 0:
                topics = [topic['name'] for topic in response[0].get('topics', [])]
                logger.info(f"Found {len(topics)} topics")
                return topics
            return []
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return []
    
    def drop_stream(self, stream_name: str, delete_topic: bool = False) -> bool:
        """
        Drop a stream from ksqlDB.
        
        Args:
            stream_name: Name of the stream to drop
            delete_topic: Whether to delete the underlying topic
            
        Returns:
            bool: True if stream was dropped successfully
        """
        try:
            query = f"DROP STREAM {stream_name}"
            if delete_topic:
                query += " DELETE TOPIC"
            query += ";"
            
            response = self.execute_query(query)
            if response:
                logger.info(f"Successfully dropped stream '{stream_name}'")
                return True
            else:
                logger.error(f"Failed to drop stream '{stream_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error dropping stream '{stream_name}': {e}")
            return False
    
    def drop_table(self, table_name: str, delete_topic: bool = False) -> bool:
        """
        Drop a table from ksqlDB.
        
        Args:
            table_name: Name of the table to drop
            delete_topic: Whether to delete the underlying topic
            
        Returns:
            bool: True if table was dropped successfully
        """
        try:
            query = f"DROP TABLE {table_name}"
            if delete_topic:
                query += " DELETE TOPIC"
            query += ";"
            
            response = self.execute_query(query)
            if response:
                logger.info(f"Successfully dropped table '{table_name}'")
                return True
            else:
                logger.error(f"Failed to drop table '{table_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error dropping table '{table_name}': {e}")
            return False
    
    def drop_connector(self, connector_name: str) -> bool:
        """
        Drop a connector from ksqlDB.
        
        Args:
            connector_name: Name of the connector to drop
            
        Returns:
            bool: True if connector was dropped successfully
        """
        try:
            query = f"DROP CONNECTOR {connector_name};"
            
            response = self.execute_query(query)
            if response:
                logger.info(f"Successfully dropped connector '{connector_name}'")
                return True
            else:
                logger.error(f"Failed to drop connector '{connector_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error dropping connector '{connector_name}': {e}")
            return False
    
    def describe_stream(self, stream_name: str) -> Optional[Dict]:
        """
        Get detailed information about a stream.
        
        Args:
            stream_name: Name of the stream to describe
            
        Returns:
            Dict: Stream description or None if failed
        """
        try:
            query = f"DESCRIBE {stream_name};"
            response = self.execute_query(query)
            return response
        except Exception as e:
            logger.error(f"Error describing stream '{stream_name}': {e}")
            return None
    
    def describe_table(self, table_name: str) -> Optional[Dict]:
        """
        Get detailed information about a table.
        
        Args:
            table_name: Name of the table to describe
            
        Returns:
            Dict: Table description or None if failed
        """
        try:
            query = f"DESCRIBE {table_name};"
            response = self.execute_query(query)
            return response
        except Exception as e:
            logger.error(f"Error describing table '{table_name}': {e}")
            return None
    
    def get_server_info(self) -> Optional[Dict]:
        """
        Get ksqlDB server information.
        
        Returns:
            Dict: Server information or None if failed
        """
        try:
            response = requests.get(f"{self.ksqldb_url}/info", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Perform a health check on the ksqlDB server.
        
        Returns:
            bool: True if server is healthy
        """
        try:
            info = self.get_server_info()
            if info:
                logger.info("ksqlDB server is healthy")
                return True
            else:
                logger.error("ksqlDB server health check failed")
                return False
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return False 
