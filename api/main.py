from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from api.schemas import TaskRequest, TaskResult
from api.auth import verify_api_key
from uuid import uuid4
import logging
import os
from prometheus_fastapi_instrumentator import Instrumentator
from agent.core import ReasoningAgent
from agent.plugins.llm_openai import OpenAILLM
from agent.plugins.kg_sqlalchemy import SQLAlchemyKG
from agent.plugins.vector_chroma import ChromaVectorStore
from agent.metrics import PrintMetrics
from agent.prompt_builder import PromptBuilder
from agent.plugin_loader import load_plugins
from agent.logging_config import logger

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# In-memory task store and websocket connections
tasks = {}
ws_connections = {}

# Instantiate plugins and agent (in real use, load from config)
llm, kg, vector_store, metrics, prompt_builder = load_plugins()
agent = ReasoningAgent(llm, kg, vector_store, metrics, prompt_builder)

def process_task(task_id, task_input):
    logger.info(f"Processing task {task_id}")
    try:
        result = agent.handle_task(task_input)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        # Notify websocket clients
        if task_id in ws_connections:
            for ws in ws_connections[task_id]:
                try:
                    import asyncio
                    asyncio.create_task(ws.send_json({"status": "completed", "result": result}))
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = str(e)

@app.post("/tasks", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def submit_task(task: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    tasks[task_id] = {"status": "pending", "result": None}
    background_tasks.add_task(process_task, task_id, task.input)
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.get("/tasks/{task_id}", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    ws_connections.setdefault(task_id, []).append(websocket)
    try:
        # Send initial status
        if task_id in tasks:
            await websocket.send_json({"status": tasks[task_id]["status"], "result": tasks[task_id]["result"]})
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        ws_connections[task_id].remove(websocket)