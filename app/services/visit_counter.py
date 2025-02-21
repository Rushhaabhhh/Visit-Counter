from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta
from ..core.redis_manager import RedisManager

class VisitCounterService:
    _instance: Optional['VisitCounterService'] = None
    _initialized = False
    
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        if not VisitCounterService._initialized:
            self.redis_manager = RedisManager()
            self.local_cache: Dict[str, tuple[int, datetime]] = {}
            self.write_buffer: Dict[str, int] = {}
            self.cache_ttl = timedelta(seconds=5)
            self.flush_interval = 30
            self._flush_task = None
            VisitCounterService._initialized = True
            VisitCounterService._instance = self

    @classmethod
    def get_instance(cls) -> 'VisitCounterService':
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start_background_tasks(self):
        """Start background flush task if not already running"""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page

        Args:
            page_id: Unique identifier for the page
        """
        # Ensure background task is running
        await self.start_background_tasks()
        
        # Add to write buffer
        self.write_buffer[page_id] = self.write_buffer.get(page_id, 0) + 1
        
        # Update local cache if it exists
        if page_id in self.local_cache:
            count, _ = self.local_cache[page_id]
            self.local_cache[page_id] = (count + 1, datetime.now())

    async def get_visit_count(self, page_id: str) -> dict:
        """
        Get current visit count for a page

        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Dict containing visit count and source information
        """
        # Ensure background task is running
        await self.start_background_tasks()
        
        # Check local cache first
        if page_id in self.local_cache:
            count, timestamp = self.local_cache[page_id]
            if datetime.now() - timestamp < self.cache_ttl:
                # Add any pending writes from buffer
                pending_count = self.write_buffer.get(page_id, 0)
                return {
                    "visits": count + pending_count,
                    "served_via": "in_memory"
                }
        
        # Cache miss or expired, get from Redis
        # First, flush pending writes
        await self._flush_key(page_id)
        
        # Get updated count from Redis
        count = await self.redis_manager.get(page_id) or 0
        
        # Update local cache
        self.local_cache[page_id] = (count, datetime.now())
        
        # Determine which Redis instance served the request
        node = self.redis_manager.consistent_hash.get_node(page_id)
        served_via = "redis_7070" if "7070" in node else "redis_7071"
        
        return {
            "visits": count,
            "served_via": served_via
        }

    async def _periodic_flush(self) -> None:
        """Periodically flush write buffer to Redis"""
        try:
            while True:
                await asyncio.sleep(self.flush_interval)
                await self._flush_all()
        except asyncio.CancelledError:
            # Ensure final flush on shutdown
            await self._flush_all()

    async def _flush_key(self, key: str) -> None:
        """Flush a specific key's pending writes to Redis"""
        if key in self.write_buffer and self.write_buffer[key] > 0:
            await self.redis_manager.increment(key, self.write_buffer[key])
            del self.write_buffer[key]

    async def _flush_all(self) -> None:
        """Flush all pending writes to Redis"""
        for key, count in list(self.write_buffer.items()):
            if count > 0:
                await self.redis_manager.increment(key, count)
        self.write_buffer.clear()