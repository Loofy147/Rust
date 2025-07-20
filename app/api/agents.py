from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.models.organization import Organization
import uuid
from datetime import datetime
from app.main import orchestrator_ai

router = APIRouter(prefix="/agents", tags=["agents"])

class AgentCreate(BaseModel):
    name: str
    type: str
    org_id: str
    config: dict = {}

class AgentOut(BaseModel):
    id: str
    name: str
    type: str
    org_id: str
    status: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=AgentOut)
def register_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = Agent(
        id=uuid.uuid4(),
        name=agent.name,
        type=agent.type,
        org_id=agent.org_id,
        config=agent.config,
        status="stopped",
        created_at=datetime.utcnow(),
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    # Register with orchestrator (stub: use agent name as key)
    orchestrator_ai.register_agent(agent.name, db_agent)
    return AgentOut(
        id=str(db_agent.id),
        name=db_agent.name,
        type=db_agent.type,
        org_id=str(db_agent.org_id),
        status=db_agent.status,
    )

@router.get("/", response_model=List[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return [AgentOut(
        id=str(a.id),
        name=a.name,
        type=a.type,
        org_id=str(a.org_id),
        status=a.status,
    ) for a in agents]

@router.post("/{agent_id}/start")
def start_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "running"
    db.commit()
    # TODO: Actually start agent process/thread if needed
    return {"status": "started", "agent_id": agent_id}

@router.post("/{agent_id}/stop")
def stop_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "stopped"
    db.commit()
    # TODO: Actually stop agent process/thread if needed
    return {"status": "stopped", "agent_id": agent_id}

@router.get("/{agent_id}/status")
def agent_status(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent_id": agent_id, "status": agent.status}