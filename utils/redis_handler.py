import redis
import json
import logging
from typing import Optional, Dict, List, Any, Union, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pickle
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisHandler:
    """
    Redis handler class using redis-py to manage Redis operations.
    
    This class provides methods to:
    - Connect to Redis with various configuration options
    - Perform key-value operations (get, set, delete, exists)
    - Manage lists, sets, and hashes
    - Handle pub/sub messaging
    - Manage TTL and expiration
    - Perform bulk operations
    - Monitor Redis status and health
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        max_connections: int = 10,
        decode_responses: bool = True
    ):
        """
        Initialize Redis handler with connection parameters.
        
        Args:
            host: Redis host address
            port: Redis port number
            db: Redis database number
            password: Redis password (if authentication is enabled)
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_connections: Maximum number of connections in the pool
            decode_responses: Whether to decode responses to strings
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        
        # Initialize Redis connection pool
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        
        # Initialize Redis client
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """
        Test the connection to Redis server.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            self.client.ping()
            logger.info(f"Successfully connected to Redis server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((redis.ConnectionError, redis.TimeoutError)),
        reraise=True
    )
    def execute_operation(self, operation_func, *args, **kwargs):
        """
        Execute a Redis operation with retry mechanism.
        
        Args:
            operation_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
        """
        return operation_func(*args, **kwargs)
    
    # Key-Value Operations
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if not a string)
            ttl: Time to live in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            bool: True if successful
        """
        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            result = self.execute_operation(
                self.client.set,
                key,
                value,
                ex=ttl,
                nx=nx,
                xx=xx
            )
            
            if result:
                logger.debug(f"Successfully set key '{key}'")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set key '{key}': {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis by key.
        
        Args:
            key: Redis key
            default: Default value if key doesn't exist
            
        Returns:
            Value associated with the key, or default if not found
        """
        try:
            value = self.execute_operation(self.client.get, key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Failed to get key '{key}': {e}")
            return default
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        try:
            result = self.execute_operation(self.client.delete, *keys)
            logger.debug(f"Deleted {result} keys: {keys}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete keys {keys}: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """
        Check if one or more keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            int: Number of keys that exist
        """
        try:
            return self.execute_operation(self.client.exists, *keys)
        except Exception as e:
            logger.error(f"Failed to check existence of keys {keys}: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            result = self.execute_operation(self.client.expire, key, ttl)
            logger.debug(f"Set TTL {ttl}s for key '{key}'")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set TTL for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get the remaining time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return self.execute_operation(self.client.ttl, key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key '{key}': {e}")
            return -2
    
    # List Operations
    def lpush(self, key: str, *values: Any) -> int:
        """
        Push values to the left of a list.
        
        Args:
            key: Redis key
            *values: Values to push
            
        Returns:
            int: Length of the list after push
        """
        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)
            
            result = self.execute_operation(self.client.lpush, key, *serialized_values)
            logger.debug(f"Pushed {len(values)} values to left of list '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to lpush to key '{key}': {e}")
            return 0
    
    def rpush(self, key: str, *values: Any) -> int:
        """
        Push values to the right of a list.
        
        Args:
            key: Redis key
            *values: Values to push
            
        Returns:
            int: Length of the list after push
        """
        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)
            
            result = self.execute_operation(self.client.rpush, key, *serialized_values)
            logger.debug(f"Pushed {len(values)} values to right of list '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to rpush to key '{key}': {e}")
            return 0
    
    def lpop(self, key: str, count: int = 1) -> Union[Any, List[Any]]:
        """
        Pop values from the left of a list.
        
        Args:
            key: Redis key
            count: Number of values to pop
            
        Returns:
            Popped value(s)
        """
        try:
            result = self.execute_operation(self.client.lpop, key, count)
            
            if result is None:
                return None
            
            # Deserialize values
            if isinstance(result, list):
                deserialized = []
                for value in result:
                    try:
                        deserialized.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        deserialized.append(value)
                return deserialized
            else:
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to lpop from key '{key}': {e}")
            return None
    
    def rpop(self, key: str, count: int = 1) -> Union[Any, List[Any]]:
        """
        Pop values from the right of a list.
        
        Args:
            key: Redis key
            count: Number of values to pop
            
        Returns:
            Popped value(s)
        """
        try:
            result = self.execute_operation(self.client.rpop, key, count)
            
            if result is None:
                return None
            
            # Deserialize values
            if isinstance(result, list):
                deserialized = []
                for value in result:
                    try:
                        deserialized.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        deserialized.append(value)
                return deserialized
            else:
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to rpop from key '{key}': {e}")
            return None
    
    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get a range of elements from a list.
        
        Args:
            key: Redis key
            start: Start index
            end: End index
            
        Returns:
            List of values
        """
        try:
            result = self.execute_operation(self.client.lrange, key, start, end)
            
            # Deserialize values
            deserialized = []
            for value in result:
                try:
                    deserialized.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    deserialized.append(value)
            
            return deserialized
        except Exception as e:
            logger.error(f"Failed to lrange from key '{key}': {e}")
            return []
    
    def llen(self, key: str) -> int:
        """
        Get the length of a list.
        
        Args:
            key: Redis key
            
        Returns:
            int: Length of the list
        """
        try:
            return self.execute_operation(self.client.llen, key)
        except Exception as e:
            logger.error(f"Failed to get length of list '{key}': {e}")
            return 0
    
    # Set Operations
    def sadd(self, key: str, *values: Any) -> int:
        """
        Add values to a set.
        
        Args:
            key: Redis key
            *values: Values to add
            
        Returns:
            int: Number of values added
        """
        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)
            
            result = self.execute_operation(self.client.sadd, key, *serialized_values)
            logger.debug(f"Added {result} values to set '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to sadd to key '{key}': {e}")
            return 0
    
    def srem(self, key: str, *values: Any) -> int:
        """
        Remove values from a set.
        
        Args:
            key: Redis key
            *values: Values to remove
            
        Returns:
            int: Number of values removed
        """
        try:
            # Serialize values if they're not strings
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)
            
            result = self.execute_operation(self.client.srem, key, *serialized_values)
            logger.debug(f"Removed {result} values from set '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to srem from key '{key}': {e}")
            return 0
    
    def smembers(self, key: str) -> set:
        """
        Get all members of a set.
        
        Args:
            key: Redis key
            
        Returns:
            set: Set of values
        """
        try:
            result = self.execute_operation(self.client.smembers, key)
            
            # Deserialize values
            deserialized = set()
            for value in result:
                try:
                    deserialized.add(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    deserialized.add(value)
            
            return deserialized
        except Exception as e:
            logger.error(f"Failed to get members of set '{key}': {e}")
            return set()
    
    def sismember(self, key: str, value: Any) -> bool:
        """
        Check if a value is a member of a set.
        
        Args:
            key: Redis key
            value: Value to check
            
        Returns:
            bool: True if value is a member
        """
        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            return bool(self.execute_operation(self.client.sismember, key, value))
        except Exception as e:
            logger.error(f"Failed to check membership in set '{key}': {e}")
            return False
    
    # Hash Operations
    def hset(self, key: str, field: str, value: Any) -> int:
        """
        Set a field in a hash.
        
        Args:
            key: Redis key
            field: Hash field
            value: Value to set
            
        Returns:
            int: 1 if field was set, 0 if field already existed
        """
        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            result = self.execute_operation(self.client.hset, key, field, value)
            logger.debug(f"Set field '{field}' in hash '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to hset field '{field}' in hash '{key}': {e}")
            return 0
    
    def hget(self, key: str, field: str, default: Any = None) -> Any:
        """
        Get a field from a hash.
        
        Args:
            key: Redis key
            field: Hash field
            default: Default value if field doesn't exist
            
        Returns:
            Value of the field, or default if not found
        """
        try:
            value = self.execute_operation(self.client.hget, key, field)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Failed to hget field '{field}' from hash '{key}': {e}")
            return default
    
    def hgetall(self, key: str) -> Dict[str, Any]:
        """
        Get all fields and values from a hash.
        
        Args:
            key: Redis key
            
        Returns:
            dict: Dictionary of field-value pairs
        """
        try:
            result = self.execute_operation(self.client.hgetall, key)
            
            # Deserialize values
            deserialized = {}
            for field, value in result.items():
                try:
                    deserialized[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    deserialized[field] = value
            
            return deserialized
        except Exception as e:
            logger.error(f"Failed to hgetall from hash '{key}': {e}")
            return {}
    
    def hdel(self, key: str, *fields: str) -> int:
        """
        Delete fields from a hash.
        
        Args:
            key: Redis key
            *fields: Fields to delete
            
        Returns:
            int: Number of fields deleted
        """
        try:
            result = self.execute_operation(self.client.hdel, key, *fields)
            logger.debug(f"Deleted {result} fields from hash '{key}'")
            return result
        except Exception as e:
            logger.error(f"Failed to hdel fields from hash '{key}': {e}")
            return 0
    
    # Pub/Sub Operations
    def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            int: Number of subscribers that received the message
        """
        try:
            # Serialize message if it's not a string
            if not isinstance(message, str):
                message = json.dumps(message)
            
            result = self.execute_operation(self.client.publish, channel, message)
            logger.debug(f"Published message to channel '{channel}'")
            return result
        except Exception as e:
            logger.error(f"Failed to publish to channel '{channel}': {e}")
            return 0
    
    def subscribe(self, *channels: str) -> redis.client.PubSub:
        """
        Subscribe to channels.
        
        Args:
            *channels: Channel names to subscribe to
            
        Returns:
            PubSub object
        """
        try:
            pubsub = self.client.pubsub()
            self.execute_operation(pubsub.subscribe, *channels)
            logger.debug(f"Subscribed to channels: {channels}")
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channels {channels}: {e}")
            return None
    
    # Utility Operations
    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: Pattern to match keys
            
        Returns:
            List of matching keys
        """
        try:
            return self.execute_operation(self.client.keys, pattern)
        except Exception as e:
            logger.error(f"Failed to get keys with pattern '{pattern}': {e}")
            return []
    
    def flushdb(self) -> bool:
        """
        Flush the current database.
        
        Returns:
            bool: True if successful
        """
        try:
            self.execute_operation(self.client.flushdb)
            logger.info("Flushed current database")
            return True
        except Exception as e:
            logger.error(f"Failed to flush database: {e}")
            return False
    
    def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Redis server information.
        
        Args:
            section: Specific section of info to retrieve
            
        Returns:
            dict: Redis server information
        """
        try:
            return self.execute_operation(self.client.info, section)
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    def ping(self) -> bool:
        """
        Ping Redis server.
        
        Returns:
            bool: True if server responds
        """
        try:
            result = self.execute_operation(self.client.ping)
            return result == b'PONG' or result == 'PONG'
        except Exception as e:
            logger.error(f"Failed to ping Redis: {e}")
            return False
    
    def close(self):
        """
        Close the Redis connection.
        """
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 
