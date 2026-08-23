"""
Redis Handler Example

This example demonstrates how to use the RedisHandler class for various Redis operations.
"""

import logging
from datetime import datetime

from redis_handler import RedisHandler
from redis_config import get_redis_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def basic_operations_example():
    """Demonstrate basic key-value operations."""
    print("\n=== Basic Key-Value Operations ===")
    
    # Initialize Redis handler
    config = get_redis_config()
    redis_handler = RedisHandler(**config)
    
    try:
        # Set a simple key-value pair
        redis_handler.set("user:1", "John Doe")
        print("✓ Set user:1 = John Doe")
        
        # Set with TTL (expires in 60 seconds)
        redis_handler.set("temp:session", "session_data", ttl=60)
        print("✓ Set temp:session with 60s TTL")
        
        # Set complex data (automatically JSON serialized)
        user_data = {
            "id": 1,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "created_at": datetime.now().isoformat()
        }
        redis_handler.set("user:2", user_data)
        print("✓ Set user:2 with complex data")
        
        # Get values
        user1 = redis_handler.get("user:1")
        user2 = redis_handler.get("user:2")
        print(f"✓ Retrieved user:1 = {user1}")
        print(f"✓ Retrieved user:2 = {user2}")
        
        # Check if keys exist
        exists = redis_handler.exists("user:1", "user:2", "nonexistent")
        print(f"✓ Keys exist: {exists}")
        
        # Get TTL
        ttl = redis_handler.ttl("temp:session")
        print(f"✓ TTL for temp:session: {ttl}s")
        
    except Exception as e:
        logger.error(f"Error in basic operations: {e}")
    finally:
        redis_handler.close()


def main():
    """Run all examples."""
    print("Redis Handler Examples")
    print("=" * 50)
    
    try:
        # Test connection first
        config = get_redis_config()
        redis_handler = RedisHandler(**config)
        if not redis_handler.ping():
            print("❌ Cannot connect to Redis. Please ensure Redis is running.")
            return
        redis_handler.close()
        
        # Run examples
        basic_operations_example()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")


if __name__ == "__main__":
    main() 
