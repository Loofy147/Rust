import os
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Body, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from orchestrator import AsyncOrchestrator, VectorType
from auth import create_token, decode_token, authenticate_user
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import numpy as np
import json
import httpx
from external_ai_agent import external_ai_agent

app = FastAPI()
orchestrator = AsyncOrchestrator()
loop = asyncio.get_event_loop()
loop.run_until_complete(orchestrator.setup())

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/orchestrator/login")

@app.post("/orchestrator/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(form_data.username, user["tenant"])
    return {"access_token": token, "token_type": "bearer"}

async def get_current_tenant(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    return payload.get("tenant", "default")

@app.post("/orchestrator/submit")
async def submit_task(
    data: list = Body(...),
    vector_type: str = Body("embedding"),
    tenant: str = Depends(get_current_tenant),
    token: str = Depends(oauth2_scheme)
):
    task = {
        "data": data,
        "vector_type": vector_type,
        "jwt": token
    }
    import queue as redis_queue
    redis_queue.enqueue_task(task)
    return {"status": "queued"}

@app.get("/orchestrator/metrics")
async def get_metrics(token: str = Depends(oauth2_scheme)):
    return orchestrator.metrics

@app.get("/orchestrator/health")
async def health():
    return {"status": "ok"}

@app.get("/orchestrator/prometheus")
async def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Example: Outbound call to external API with OAuth2 Bearer token
@app.get("/orchestrator/external_call")
async def external_api_call(token: str = Depends(oauth2_scheme)):
    url = "https://api.external-service.com/resource"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/orchestrator/external_ai")
async def external_ai(
    tool_name: str = Body(...),
    data: dict = Body(...),
    parameters: dict = Body({}),
    token: str = Depends(oauth2_scheme)
):
    result = await external_ai_agent.call_tool(tool_name, data, parameters)
    return result