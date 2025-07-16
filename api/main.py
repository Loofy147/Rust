from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from api.schemas import TaskRequest, TaskResult
from api.auth import verify_api_key
from uuid import uuid4
import os
from prometheus_fastapi_instrumentator import Instrumentator
from agent.plugin_loader import load_plugins
from agent.logging_config import logger
from celery.result import AsyncResult
from celery_worker import process_task_celery, celery_app

app = FastAPI()
Instrumentator().instrument(app).expose(app)

tasks = {}
ws_connections = {}

llm, kg, vector_store, metrics, prompt_builder = load_plugins()

@app.post("/tasks", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def submit_task(task: TaskRequest):
    task_id = str(uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "celery_id": None}
    celery_result = process_task_celery.apply_async(args=[task_id, task.input])
    tasks[task_id]["celery_id"] = celery_result.id
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.get("/tasks/{task_id}", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    celery_id = tasks[task_id]["celery_id"]
    result = AsyncResult(celery_id, app=celery_app)
    if result.ready():
        try:
            output = result.get()
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = output["result"]
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["result"] = str(e)
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    ws_connections.setdefault(task_id, []).append(websocket)
    try:
        # Send initial status
        if task_id in tasks:
            await websocket.send_json({"status": tasks[task_id]["status"], "result": tasks[task_id]["result"]})
        celery_id = tasks[task_id]["celery_id"]
        result = AsyncResult(celery_id, app=celery_app)
        while not result.ready():
            await websocket.receive_text()  # Keep connection open
        try:
            output = result.get()
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = output["result"]
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["result"] = str(e)
        await websocket.send_json({"status": tasks[task_id]["status"], "result": tasks[task_id]["result"]})
    except WebSocketDisconnect:
        ws_connections[task_id].remove(websocket)