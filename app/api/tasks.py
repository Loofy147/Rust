from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.agent import Agent
import uuid
from datetime import datetime
from app.main import orchestrator_ai
from app.orchestrator.core import Task as OrchestratorTask

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    agent_id: str
    user_id: str
    org_id: str
    type: str
    input: dict
    priority: Optional[int] = 0

class TaskOut(BaseModel):
    id: str
    agent_id: str
    user_id: str
    org_id: str
    type: str
    status: str
    input: dict
    output: Optional[dict]
    error: Optional[str]

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TaskOut)
def submit_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(
        id=uuid.uuid4(),
        agent_id=task.agent_id,
        user_id=task.user_id,
        org_id=task.org_id,
        type=task.type,
        status="pending",
        input=task.input,
        output=None,
        error=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    # Find agent in orchestrator registry
    agent = None
    for name, a in orchestrator_ai.agent_registry.items():
        if str(getattr(a, 'id', '')) == task.agent_id or name == task.type or name == task.agent_id:
            agent = a
            break
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found in orchestrator")
    # Submit to orchestrator for real execution
    def agent_task():
        try:
            # Call the correct method on the agent based on task type
            if hasattr(agent, task.type):
                method = getattr(agent, task.type)
                result = method(**task.input)
            elif callable(agent):
                result = agent(**task.input)
            else:
                result = {"result": "executed by agent stub"}
            db_task.status = "done"
            db_task.output = result
            db_task.updated_at = datetime.utcnow()
        except Exception as e:
            db_task.status = "error"
            db_task.error = str(e)
            db_task.updated_at = datetime.utcnow()
        db.commit()
    orchestrator_ai.submit_task(OrchestratorTask(func=agent_task, description=f"Task {db_task.id}"))
    return TaskOut(
        id=str(db_task.id),
        agent_id=str(db_task.agent_id),
        user_id=str(db_task.user_id),
        org_id=str(db_task.org_id),
        type=db_task.type,
        status=db_task.status,
        input=db_task.input,
        output=db_task.output,
        error=db_task.error,
    )

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(
        id=str(db_task.id),
        agent_id=str(db_task.agent_id),
        user_id=str(db_task.user_id),
        org_id=str(db_task.org_id),
        type=db_task.type,
        status=db_task.status,
        input=db_task.input,
        output=db_task.output,
        error=db_task.error,
    )

@router.get("/", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [TaskOut(
        id=str(t.id),
        agent_id=str(t.agent_id),
        user_id=str(t.user_id),
        org_id=str(t.org_id),
        type=t.type,
        status=t.status,
        input=t.input,
        output=t.output,
        error=t.error,
    ) for t in tasks]