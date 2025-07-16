import os
import uuid
import asyncio
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
from typing import Dict, Any

# Config
KG_API_URL = os.getenv("KG_API_URL", "http://kg_api:8000")

app = FastAPI()
Instrumentator().instrument(app).expose(app)
logger = logging.getLogger("ReasoningAgentService")

# In-memory task store (for demo)
tasks: Dict[str, Dict[str, Any]] = {}

# Auth (reuse from kg_api if needed)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class TaskRequest(BaseModel):
    input: str
    context: Dict[str, Any] = {}
    rules: list = []
    trace: bool = False

class TaskResult(BaseModel):
    id: str
    status: str
    result: Any = None

@app.post("/tasks", response_model=TaskResult)
async def submit_task(task: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None}
    background_tasks.add_task(process_task, task_id, task)
    return TaskResult(id=task_id, status="pending")

async def process_task(task_id: str, task: TaskRequest):
    try:
        # Call KG reasoning endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KG_API_URL}/reasoning",
                params={
                    "query": task.input,
                    "trace": str(task.trace).lower(),
                    # Optionally pass rules/context as JSON strings
                },
                timeout=60.0
            )
            if resp.status_code == 200:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = resp.json()
            else:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["result"] = resp.text
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = str(e)

@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}")
    return JSONResponse(status_code=500, content={"error": {"code": 500, "message": str(exc)}})