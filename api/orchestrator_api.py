import os
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Body, Header
from orchestrator import AsyncOrchestrator, VectorType
from auth import decode_token
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import numpy as np
import json

app = FastAPI()
orchestrator = AsyncOrchestrator()
loop = asyncio.get_event_loop()
loop.run_until_complete(orchestrator.setup())

# JWT Auth dependency
async def get_tenant(authorization: str = Header(...)):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split()[1]
    payload = decode_token(token)
    return payload.get("tenant", "default")

@app.post("/orchestrator/submit")
async def submit_task(
    data: list = Body(...),
    vector_type: str = Body("embedding"),
    tenant: str = Depends(get_tenant),
    authorization: str = Header(...)
):
    # Accepts a list of lists (vector data)
    task = {
        "data": data,
        "vector_type": vector_type,
        "jwt": authorization.split()[1]
    }
    # Enqueue to Redis
    import queue as redis_queue
    redis_queue.enqueue_task(task)
    return {"status": "queued"}

@app.get("/orchestrator/metrics")
def get_metrics():
    return orchestrator.metrics

@app.get("/orchestrator/health")
def health():
    return {"status": "ok"}

@app.get("/orchestrator/prometheus")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)