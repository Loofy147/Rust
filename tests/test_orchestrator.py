import pytest
from app.orchestrator.core import OrchestratorAI

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    orchestrator = OrchestratorAI()
    assert orchestrator is not None
