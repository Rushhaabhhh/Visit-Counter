# from typing import Dict, List, Any
# import asyncio
# from datetime import datetime
from ..core.redis_manager import RedisManager

class VisitCounterService:
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()
    
    def increment_visit(self, page_id: str):
        """Increment visit count for a page"""
        return self.redis_manager.increment(page_id)
    
    def get_visit_count(self, page_id: str) -> int:
        """Get current visit count for a page"""
        return self.redis_manager.get(page_id)

if __name__ == "__main__":
    visit_service = VisitCounterService()
    visit_service.increment_visit("page1")
    count = visit_service.get_visit_count("page1")
    print("Total visits to page1:", count)

