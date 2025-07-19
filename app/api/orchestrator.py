from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.orchestrator.core import OrchestratorAI

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

# Assume orchestrator_ai is imported or injected
orchestrator_ai: Optional[OrchestratorAI] = None

class ScaleRequest(BaseModel):
    max_workers: int

@router.get("/status")
def get_status():
    if orchestrator_ai:
        return orchestrator_ai.get_status()
    return {"status": "not initialized"}

@router.post("/scale")
def scale_orchestrator(req: ScaleRequest):
    if orchestrator_ai:
        orchestrator_ai.executor._max_workers = req.max_workers
        return {"max_workers": req.max_workers}
    return {"status": "not initialized"}

@router.post("/submit_workflow")
def submit_workflow():
    # TODO: Implement workflow submission logic
    return {"status": "workflow submitted"}