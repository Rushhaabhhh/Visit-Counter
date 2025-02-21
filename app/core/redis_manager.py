import redis
# from typing import Dict, List, Optional, Any
from .consistent_hash import ConsistentHash
from .config import settings

class RedisManager:
    def __init__(self):
        """Initialize Redis connection pools and consistent hashing"""
        self.connection_pools = {}
        self.redis_clients = {}
        
        redis_nodes = [node.strip() for node in settings.REDIS_NODES.split(",") if node.strip()]
        self.consistent_hash = ConsistentHash(redis_nodes, settings.VIRTUAL_NODES)
        
        for node in redis_nodes:
            try:
                self.connection_pools[node] = redis.ConnectionPool(host=node, port=6379, decode_responses=True)
                self.redis_clients[node] = redis.Redis(connection_pool=self.connection_pools[node])
            except redis.ConnectionError as e:
                print(f"Error connecting to Redis node {node}: {e}")
    
    def get_connection(self, key: str):
        """Get Redis connection for the given key using consistent hashing"""
        node = self.consistent_hash.get_node(key)
        return self.redis_clients.get(node)
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in Redis"""
        client = self.get_connection(key)
        if client:
            return client.incrby(key, amount)
        return 0
    
    def get(self, key: str):
        """Get value for a key from Redis"""
        client = self.get_connection(key)
        if client:
            value = client.get(key)
            return int(value) if value else 0
        return 0