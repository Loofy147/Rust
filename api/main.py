from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import importlib

# Import the Rust extension (built by maturin)
try:
    reasoning_agent = importlib.import_module("reasoning_agent")
except ImportError:
    reasoning_agent = None

app = FastAPI(title="ReasoningAgent API")

class TaskRequest(BaseModel):
    prompt: str
    model: str = "text-davinci-003"
    max_tokens: int = 256
    temperature: float = 0.7

class TaskResponse(BaseModel):
    answer: str

@app.post("/task", response_model=TaskResponse)
def submit_task(req: TaskRequest):
    if not reasoning_agent:
        raise HTTPException(status_code=500, detail="Rust extension not loaded")
    try:
        answer = reasoning_agent.call_openai(
            req.prompt, req.model, req.max_tokens, req.temperature
        )
        return TaskResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    # Placeholder for Prometheus or custom metrics
    return {"status": "ok", "tasks_processed": 0}

@app.get("/query")
def query():
    # Placeholder for querying previous answers (to be implemented with persistence)
    return {"message": "Query endpoint not yet implemented."}