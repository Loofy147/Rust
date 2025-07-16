from fastapi import FastAPI, HTTPException, Depends
from api.schemas import TaskRequest, TaskResult
from api.auth import verify_api_key
from uuid import uuid4

app = FastAPI()
tasks = {}

@app.post("/tasks", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def submit_task(task: TaskRequest):
    task_id = str(uuid4())
    # In a real system, enqueue for background processing
    tasks[task_id] = {"status": "pending", "result": None}
    # Simulate immediate processing for demo
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["result"] = f"Processed: {task.input}"
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.get("/tasks/{task_id}", response_model=TaskResult, dependencies=[Depends(verify_api_key)])
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])