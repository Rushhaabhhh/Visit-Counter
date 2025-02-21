import hashlib
# from typing import List, Dict, Any
# from bisect import bisect_left

class ConsistentHash:
    def __init__(self, nodes=None, replicas=3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    
    def add_node(self, node):
        for i in range(self.replicas):
            hash_value = self._hash(f"{node}:{i}")
            self.ring[hash_value] = node
            self.sorted_keys.append(hash_value)
        self.sorted_keys.sort()
    
    def get_node(self, key):
        hash_value = self._hash(key)
        for h in self.sorted_keys:
            if hash_value <= h:
                return self.ring[h]
        return self.ring[self.sorted_keys[0]]