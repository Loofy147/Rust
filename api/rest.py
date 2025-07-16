from fastapi import FastAPI, Depends, HTTPException, Header, Body
from storage.base import get_storage_backend
import yaml
from agents.registry import AgentRegistry
from plugins.plugin_manager import PluginManager
from main import agent_registry, plugin_manager, task_queue_agent

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