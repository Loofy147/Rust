from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

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