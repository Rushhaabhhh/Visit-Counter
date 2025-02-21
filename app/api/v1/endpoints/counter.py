from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ....services.visit_counter import VisitCounterService
from ....schemas.counter import VisitCount

router = APIRouter()

def get_visit_counter_service():
    """Dependency to get VisitCounterService instance"""
    return VisitCounterService.get_instance()

@router.post("/visit/{page_id}")
async def increment_visit(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service)
):
    await counter_service.increment_visit(page_id)
    return {"status": "success"}

@router.get("/visits/{page_id}")
async def get_visits(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service)
):
    return await counter_service.get_visit_count(page_id)