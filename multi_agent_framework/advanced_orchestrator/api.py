from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# These would be injected from orchestrator
REGISTRY = None
WORKFLOW_ENGINE = None
EVENT_BUS = None

@app.post("/register_agent")
async def register_agent(request: Request):
    data = await request.json()
    REGISTRY.register(data['agent_id'], data['info'])
    return JSONResponse({"status": "registered"})

@app.post("/unregister_agent")
async def unregister_agent(request: Request):
    data = await request.json()
    REGISTRY.unregister(data['agent_id'])
    return JSONResponse({"status": "unregistered"})

@app.get("/agents")
async def list_agents():
    return REGISTRY.all()

@app.post("/submit_workflow")
async def submit_workflow(request: Request):
    data = await request.json()
    WORKFLOW_ENGINE.add_workflow(data['workflow_id'], data['steps'], dag=data.get('dag', False))
    return JSONResponse({"status": "workflow_added"})

# --- HITL approval endpoint ---
@app.post("/approve_hitl_step")
async def approve_hitl_step(request: Request):
    data = await request.json()
    WORKFLOW_ENGINE.approve_hitl_step(data['workflow_id'], data['step_id'])
    return JSONResponse({"status": "approved"})

@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    def cb(event_type, data):
        asyncio.create_task(queue.put({"event": event_type, "data": data}))
    EVENT_BUS.subscribe("update", cb)
    try:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
    except Exception:
        pass
    finally:
        EVENT_BUS.unsubscribe("update", cb)

@app.get("/plugins")
async def list_plugins():
    # Stub: Return list of available plugins (from config/plugins dir)
    return [f for f in (os.listdir('config/plugins') if os.path.exists('config/plugins') else []) if f.endswith('.py')]

@app.post("/upload_plugin")
async def upload_plugin(request: Request):
    # Stub: Accept plugin upload (not implemented)
    return JSONResponse({"status": "not_implemented"})

@app.get("/workflows")
async def list_workflows():
    # Stub: Return list of available workflows (from config dir)
    return [f for f in (os.listdir('config') if os.path.exists('config')) if f.endswith('.yaml')]

@app.post("/upload_workflow")
async def upload_workflow(request: Request):
    # Stub: Accept workflow upload (not implemented)
    return JSONResponse({"status": "not_implemented"})

@app.post("/register_edge_agent")
async def register_edge_agent(request: Request):
    data = await request.json()
    REGISTRY.register_edge_agent(data['agent_id'], data['info'], data['edge_location'])
    return JSONResponse({"status": "edge_registered"})

@app.get("/edge_agents")
async def list_edge_agents(location: str = None):
    return REGISTRY.find_edge_agents(location)