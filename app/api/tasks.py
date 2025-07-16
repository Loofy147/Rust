from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

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

@router.post("/", response_model=TaskOut)
def submit_task(task: TaskCreate):
    # TODO: Implement task submission logic
    return TaskOut(id="task-uuid", agent_id=task.agent_id, user_id=task.user_id, org_id=task.org_id, type=task.type, status="pending", input=task.input, output=None, error=None)

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    # TODO: Implement task status/result retrieval
    return TaskOut(id=task_id, agent_id="agent-uuid", user_id="user-uuid", org_id="org-uuid", type="search", status="done", input={}, output={"result": "ok"}, error=None)

@router.get("/", response_model=List[TaskOut])
def list_tasks():
    # TODO: Implement task listing
    return [TaskOut(id="task-uuid", agent_id="agent-uuid", user_id="user-uuid", org_id="org-uuid", type="search", status="done", input={}, output={"result": "ok"}, error=None)]