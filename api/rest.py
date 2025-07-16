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

# Add: node capabilities and load in heartbeat, smart assignment, task rejection, and queued tasks
QUEUED_TASKS = []

@app.post("/agents/heartbeat")
def node_heartbeat(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    capabilities = payload.get('capabilities', {})
    load = payload.get('load', 0)
    if node_id in NODES:
        NODES[node_id]['last_seen'] = time.time()
        NODES[node_id]['status'] = 'alive'
        NODES[node_id]['capabilities'] = capabilities
        NODES[node_id]['load'] = load
        return {"status": "heartbeat", "node_id": node_id}
    return {"error": "Node not registered"}

@app.post("/tasks/submit")
def submit_task(payload: dict = Body(...)):
    # Smart assignment based on capabilities and load
    required = payload.get('required', {})
    best_node = None
    best_load = float('inf')
    now = time.time()
    for node_id, info in NODES.items():
        if now - info['last_seen'] > 15:
            continue  # skip dead nodes
        caps = info.get('capabilities', {})
        if all(caps.get(k) == v for k, v in required.items()):
            node_load = info.get('load', 0)
            if node_load < best_load:
                best_node = node_id
                best_load = node_load
    if best_node:
        if best_node not in NODE_TASKS:
            NODE_TASKS[best_node] = []
        NODE_TASKS[best_node].append(payload)
        return {"status": "assigned", "node_id": best_node, "task": payload}
    else:
        QUEUED_TASKS.append(payload)
        return {"status": "queued", "reason": "no suitable node", "task": payload}

@app.post("/tasks/reject")
def reject_task(payload: dict = Body(...)):
    task = payload.get('task')
    QUEUED_TASKS.append(task)
    return {"status": "requeued", "task": task}

@app.get("/tasks/queued")
def get_queued_tasks():
    return QUEUED_TASKS

@app.get("/tasks/{task_id}", dependencies=[Depends(check_auth)])
def get_task_status(task_id: int):
    return task_queue_agent.get_task_status(task_id)

@app.post("/agents/register")
def register_node(payload: dict = Body(...)):
    node_id = payload.get('node_id')
    NODES[node_id] = {'last_seen': time.time(), 'status': 'registered'}
    return {"status": "registered", "node_id": node_id}

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