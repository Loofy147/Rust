from fastapi import FastAPI, WebSocket, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from advanced_orchestrator.orchestrator import orchestrator
import traceback
from advanced_orchestrator.monitoring import api_request_counter, api_error_counter, tracer
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

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

# Store review queue in memory for demo
REVIEW_QUEUE = []

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "trace": traceback.format_exc()
        },
    )

@app.get("/metrics")
def metrics():
    return JSONResponse(content=generate_latest().decode('utf-8'), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok"}

# Instrumented endpoints
@app.post("/register_agent")
async def register_agent(request: Request):
    with tracer.start_as_current_span("register_agent"):
        api_request_counter.labels(endpoint="/register_agent", method="POST").inc()
        try:
            data = await request.json()
            REGISTRY.register(data['agent_id'], data['info'])
            return JSONResponse({"status": "registered"})
        except Exception as e:
            api_error_counter.labels(endpoint="/register_agent", method="POST").inc()
            raise e

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

@app.get("/annotation_samples")
async def annotation_samples():
    # For demo: fetch from the first registered annotation agent
    agent = REGISTRY.get('data_annotation1')
    if agent and hasattr(agent['info'], 'instance'):
        samples = agent['info']['instance'].process({'data': ''})['pending_samples']
        return samples
    return []

@app.post("/submit_annotation")
async def submit_annotation(request: Request):
    data = await request.json()
    agent = REGISTRY.get('data_annotation1')
    user = data.get('user', 'unknown')
    if agent and hasattr(agent['info'], 'instance'):
        result = agent['info']['instance'].submit_label(data['index'], data['label'], user)
        # Add to review queue
        REVIEW_QUEUE.append({
            'index': data['index'],
            'label': data['label'],
            'user': user,
            'status': 'pending'
        })
        return result
    return {"status": "error", "reason": "No annotation agent"}

@app.get("/review_queue")
async def review_queue():
    return REVIEW_QUEUE

@app.post("/review_annotation")
async def review_annotation(request: Request):
    data = await request.json()
    for item in REVIEW_QUEUE:
        if item['index'] == data['index']:
            item['status'] = data['status']
            item['reviewer'] = data.get('reviewer', 'reviewer')
            item['review_comment'] = data.get('comment', '')
            return {"status": "reviewed"}
    return {"status": "not_found"}

@app.get("/hitl_queue")
async def hitl_queue():
    # Return pending HITL QA tasks
    return orchestrator.human_in_the_loop_queue

@app.post("/hitl_qa")
async def hitl_qa(request: Request):
    data = await request.json()
    # Find and remove the task from the queue
    for i, task in enumerate(orchestrator.human_in_the_loop_queue):
        if task.get('workflow_id') == data.get('workflow_id') and task.get('step') == data.get('step'):
            orchestrator.human_in_the_loop_queue.pop(i)
            break
    # Log feedback/action
    orchestrator.workflow_engine.log_feedback(data['workflow_id'], data['step'], {
        'action': data.get('action'),
        'edited_answer': data.get('edited_answer'),
        'feedback': data.get('feedback'),
        'user': data.get('user')
    })
    # Optionally, trigger re-processing or finalize output
    return {"status": "qa_logged"}