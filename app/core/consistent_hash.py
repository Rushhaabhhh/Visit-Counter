import hashlib
from typing import List, Dict
from bisect import bisect

class ConsistentHash:
    def __init__(self, nodes: List[str], virtual_nodes: int = 100):
        """
        Initialize the consistent hash ring

        Args:
            nodes: List of node identifiers
            virtual_nodes: Number of virtual nodes per physical node
        """
        self.virtual_nodes = virtual_nodes
        self.hash_ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        for node in nodes:
            self.add_node(node)
    
    def _hash(self, key: str) -> int:
        """Generate hash for a key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str) -> None:
        """
        Add a new node to the hash ring

        Args:
            node: Node identifier to add
        """
        for i in range(self.virtual_nodes):
            virtual_node = f"{node}#{i}"
            hash_key = self._hash(virtual_node)
            self.hash_ring[hash_key] = node
            
            # Insert hash_key into sorted_keys maintaining order
            insert_pos = bisect(self.sorted_keys, hash_key)
            self.sorted_keys.insert(insert_pos, hash_key)
    
    def remove_node(self, node: str) -> None:
        """
        Remove a node from the hash ring

        Args:
            node: Node identifier to remove
        """
        for i in range(self.virtual_nodes):
            virtual_node = f"{node}#{i}"
            hash_key = self._hash(virtual_node)
            
            if hash_key in self.hash_ring:
                del self.hash_ring[hash_key]
                self.sorted_keys.remove(hash_key)
    
    def get_node(self, key: str) -> str:
        """
        Get the node responsible for the given key

        Args:
            key: The key to look up
            
        Returns:
            The node responsible for the key
        """
        if not self.sorted_keys:
            raise Exception("Hash ring is empty")
            
        hash_key = self._hash(key)
        
        # Find the first node in the ring that comes after the key's hash
        pos = bisect(self.sorted_keys, hash_key)
        if pos == len(self.sorted_keys):
            pos = 0
            
        return self.hash_ring[self.sorted_keys[pos]]