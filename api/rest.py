from fastapi import FastAPI, Depends, HTTPException, Header, Body, Request
import yaml
from agents.registry import AgentRegistry
from plugins.plugin_manager import PluginManager
from main import agent_registry, plugin_manager, task_queue_agent
import time

# In-memory node registry and task assignment for demo
NODES = {}
NODE_TASKS = {}
TASK_RESULTS = {}

with open('config.yaml') as f:
    config = yaml.safe_load(f)

storage = get_storage_backend(config['storage'])

app = FastAPI()

def check_auth(authorization: str = Header(...)):
    if authorization != f"Bearer {config['api']['auth_token']}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/data", dependencies=[Depends(check_auth)])
def get_data():
    return storage.load()

@app.post("/data", dependencies=[Depends(check_auth)])
def add_data(item: dict):
    storage.save(item)
    return {"status": "saved"}

@app.post("/vector_search", dependencies=[Depends(check_auth)])
def vector_search(query: dict = Body(...)):
    vector = query.get('vector')
    k = query.get('k', 5)
    if hasattr(storage, 'search'):
        results = storage.search(vector, k)
        return {"results": results}
    return {"error": "Vector search not supported by current storage backend."}

@app.get("/agents", dependencies=[Depends(check_auth)])
def list_agents():
    return agent_registry.all()

@app.get("/plugins", dependencies=[Depends(check_auth)])
def list_plugins():
    return list(plugin_manager.plugins.keys())

@app.post("/plugins/load", dependencies=[Depends(check_auth)])
def load_plugin(payload: dict = Body(...)):
    module = payload.get('module')
    cls = payload.get('class')
    plugin_manager.load_plugin(module, cls)
    return {"status": "loaded", "plugin": cls}

@app.post("/plugins/unload", dependencies=[Depends(check_auth)])
def unload_plugin(payload: dict = Body(...)):
    cls = payload.get('class')
    plugin_manager.unload_plugin(cls)
    return {"status": "unloaded", "plugin": cls}

@app.post("/tasks", dependencies=[Depends(check_auth)])
def submit_task(payload: dict = Body(...)):
    priority = payload.get('priority', 10)
    task_id = task_queue_agent.add_task(payload, priority)
    return {"status": "submitted", "task_id": task_id}

@app.get("/tasks/{task_id}", dependencies=[Depends(check_auth)])
def get_task_status(task_id: int):
    return task_queue_agent.get_task_status(task_id)

@app.post("/agents/register")
def register_node(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    NODES[node_id] = {'last_seen': time.time(), 'status': 'registered'}
    return {"status": "registered", "node_id": node_id}

@app.post("/agents/heartbeat")
def node_heartbeat(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    if node_id in NODES:
        NODES[node_id]['last_seen'] = time.time()
        NODES[node_id]['status'] = 'alive'
        return {"status": "heartbeat", "node_id": node_id}
    return {"error": "Node not registered"}

@app.get("/agents/nodes")
def list_nodes():
    # Add last_seen delta for UI
    now = time.time()
    return {nid: {**info, 'last_seen_delta': now-info['last_seen']} for nid, info in NODES.items()}

@app.post("/tasks/assign")
def assign_task(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    task = payload.get('task')
    if node_id not in NODE_TASKS:
        NODE_TASKS[node_id] = []
    NODE_TASKS[node_id].append(task)
    return {"status": "assigned", "node_id": node_id, "task": task}

@app.get("/tasks/poll/{node_id}")
def poll_tasks(node_id: str):
    tasks = NODE_TASKS.get(node_id, [])
    NODE_TASKS[node_id] = []
    return {"tasks": tasks}

@app.post("/tasks/result")
def report_result(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    task_id = payload.get('task_id')
    result = payload.get('result')
    TASK_RESULTS[task_id] = {'node_id': node_id, 'result': result, 'timestamp': time.time()}
    return {"status": "result_received", "task_id": task_id}

@app.get("/tasks/results")
def get_all_results():
    return TASK_RESULTS