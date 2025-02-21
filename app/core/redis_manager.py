import asyncio
import redis
from typing import Dict, Optional
from .consistent_hash import ConsistentHash

class RedisManager:
    def __init__(self):
        """Initialize Redis connection pools and consistent hashing"""
        self.connection_pools: Dict[str, redis.ConnectionPool] = {}
        self.redis_clients: Dict[str, redis.Redis] = {}
        
        # Use Docker service names instead of localhost
        redis_nodes = [
            "redis://redis1:6379",  # First Redis instance
            "redis://redis2:6380",  # Second Redis instance
            "redis://redis3:6381"
        ]
        self.consistent_hash = ConsistentHash(redis_nodes, 100)
        
        # Initialize connection pools for each Redis node
        for node in redis_nodes:
            try:
                self.connection_pools[node] = redis.ConnectionPool.from_url(
                    node,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    max_connections=10
                )
                self.redis_clients[node] = redis.Redis(
                    connection_pool=self.connection_pools[node],
                    decode_responses=True  # Automatically decode response bytes to str
                )
            except redis.RedisError as e:
                raise Exception(f"Failed to initialize Redis connection for {node}: {str(e)}")
    
    def get_connection(self, key: str) -> redis.Redis:
        """
        Get Redis connection for the given key using consistent hashing

        Args:
            key: The key to determine which Redis node to use
            
        Returns:
            Redis client for the appropriate node
        """
        node = self.consistent_hash.get_node(key)
        if node not in self.redis_clients:
            raise Exception(f"No Redis client found for node {node}")
        return self.redis_clients[node]
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis

        Args:
            key: The key to increment
            amount: Amount to increment by
            
        Returns:
            New value of the counter
        """
        redis_client = self.get_connection(key)
        retries = 3
        
        for attempt in range(retries):
            try:
                return redis_client.incrby(key, amount)
            except redis.RedisError as e:
                if attempt == retries - 1:  # Last attempt
                    raise Exception(f"Failed to increment key {key}: {str(e)}")
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    async def get(self, key: str) -> Optional[int]:
        """
        Get value for a key from Redis

        Args:
            key: The key to get
            
        Returns:
            Value of the key or None if not found
        """
        redis_client = self.get_connection(key)
        retries = 3
        
        for attempt in range(retries):
            try:
                value = redis_client.get(key)
                return int(value) if value is not None else None
            except redis.RedisError as e:
                if attempt == retries - 1:  # Last attempt
                    raise Exception(f"Failed to get key {key}: {str(e)}")
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff