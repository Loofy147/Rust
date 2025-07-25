from fastapi import FastAPI, WebSocket, Request, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from advanced_orchestrator.orchestrator import orchestrator
import traceback
from advanced_orchestrator.monitoring import api_request_counter, api_error_counter, tracer
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
logger = logging.getLogger("audit")

users_db = {
    "annotator": {"username": "annotator", "role": "annotator", "password": "annotatorpass"},
    "reviewer": {"username": "reviewer", "role": "reviewer", "password": "reviewerpass"},
    "admin": {"username": "admin", "role": "admin", "password": "adminpass"}
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in users_db:
            raise JWTError()
        return users_db[username]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def require_role(role):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] != role and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

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

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

# Instrumented endpoints
@app.post("/register_agent")
async def register_agent(request: Request, user=Depends(require_role("admin"))):
    with tracer.start_as_current_span("register_agent"):
        api_request_counter.labels(endpoint="/register_agent", method="POST").inc()
        try:
            data = await request.json()
            REGISTRY.register(data['agent_id'], data['info'])
            logger.info(f"User {user['username']} registered agent {data['agent_id']}")
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
    plugin_dir = 'config/plugins'
    if os.path.exists(plugin_dir):
        return [f for f in os.listdir(plugin_dir) if f.endswith('.py')]
    return []

@app.post("/upload_plugin")
async def upload_plugin(request: Request):
    # Stub: Accept plugin upload (not implemented)
    return JSONResponse({"status": "not_implemented"})

@app.get("/workflows")
async def list_workflows():
    # Stub: Return list of available workflows (from config dir)
    config_dir = 'config'
    if os.path.exists(config_dir):
        return [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
    return []

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

@app.get("/workflow_history/{workflow_id}")
async def workflow_history(workflow_id: str, user=Depends(require_role("reviewer"))):
    history = orchestrator.workflow_engine.get_run_history(workflow_id)
    feedback = orchestrator.workflow_engine.get_feedback_log(workflow_id)
    return {"history": history, "feedback": feedback}

@app.get("/agent_logs/{agent_id}")
async def agent_logs(agent_id: str, user=Depends(require_role("reviewer"))):
    # For demo: return recent logs from agent (if available)
    agent = orchestrator.registry.get(agent_id)
    if agent and hasattr(agent['info'], 'instance'):
        # Assume agent instance has a logs attribute or method
        logs = getattr(agent['info']['instance'], 'logs', [])
        return {"logs": logs}
    return {"logs": []}

@app.get("/user_analytics")
async def user_analytics(user=Depends(require_role("reviewer"))):
    # For demo: count actions in feedback logs by user
    user_counts = {}
    for wf_id in orchestrator.workflow_engine._feedback_log:
        for entry in orchestrator.workflow_engine._feedback_log[wf_id]:
            u = entry.get('feedback', {}).get('user') or entry.get('user')
            if u:
                user_counts[u] = user_counts.get(u, 0) + 1
    leaderboard = sorted(user_counts.items(), key=lambda x: -x[1])
    return {"leaderboard": leaderboard}