from fastapi import FastAPI, Depends, Body, HTTPException, Header
import yaml
from db.models import Node, Task
from db.session import get_db
from sqlalchemy.orm import Session
import time
import uuid
import os
from dotenv import load_dotenv
from vector_db import SimpleFaissDB
import numpy as np

load_dotenv()
API_KEY = os.environ.get('API_KEY', 'changeme')

app = FastAPI()

with open('config.yaml') as f:
    config = yaml.safe_load(f)

def check_api_key(authorization: str = Header(...)):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

@app.post("/agents/register", dependencies=[Depends(check_api_key)])
def register_node(payload: dict = Body(...), db: Session = Depends(get_db)):
    node_id = payload.get('node_id')
    node = db.query(Node).filter_by(node_id=node_id).first()
    if not node:
        node = Node(node_id=node_id, status='registered', last_seen=time.time(), capabilities={}, load=0)
        db.add(node)
    else:
        node.status = 'registered'
        node.last_seen = time.time()
    db.commit()
    return {"status": "registered", "node_id": node_id}

@app.post("/agents/heartbeat", dependencies=[Depends(check_api_key)])
def node_heartbeat(payload: dict = Body(...), db: Session = Depends(get_db)):
    node_id = payload.get('node_id')
    capabilities = payload.get('capabilities', {})
    load = payload.get('load', 0)
    node = db.query(Node).filter_by(node_id=node_id).first()
    if node:
        node.last_seen = time.time()
        node.status = 'alive'
        node.capabilities = capabilities
        node.load = load
        db.commit()
        return {"status": "heartbeat", "node_id": node_id}
    return {"error": "Node not registered"}

@app.get("/agents/nodes", dependencies=[Depends(check_api_key)])
def list_nodes(db: Session = Depends(get_db)):
    now = time.time()
    nodes = db.query(Node).all()
    return {n.node_id: {"status": n.status, "capabilities": n.capabilities, "load": n.load, "last_seen_delta": now-n.last_seen} for n in nodes}

@app.post("/agents/deregister", dependencies=[Depends(check_api_key)])
def deregister_node(payload: dict = Body(...), db: Session = Depends(get_db)):
    node_id = payload.get('node_id')
    node = db.query(Node).filter_by(node_id=node_id).first()
    if node:
        db.delete(node)
        db.commit()
        return {"status": "deregistered", "node_id": node_id}
    return {"error": "Node not found"}

@app.post("/tasks/submit", dependencies=[Depends(check_api_key)])
def submit_task(payload: dict = Body(...), db: Session = Depends(get_db)):
    task_id = payload.get('id') or str(uuid.uuid4())
    payload['id'] = task_id
    payload['submitted_at'] = time.time()
    payload['status'] = 'queued'
    task = Task(id=task_id, status='queued', node_id=None, payload=payload, submitted_at=payload['submitted_at'], assigned_at=None, completed_at=None, result=None)
    db.add(task)
    db.commit()
    required = payload.get('required', {})
    best_node = None
    best_load = float('inf')
    now = time.time()
    for node in db.query(Node).all():
        if now - node.last_seen > 15:
            continue
        caps = node.capabilities or {}
        if all(caps.get(k) == v for k, v in required.items()):
            if node.load < best_load:
                best_node = node.node_id
                best_load = node.load
    if best_node:
        task.status = 'assigned'
        task.node_id = best_node
        task.assigned_at = now
        db.commit()
        return {"status": "assigned", "node_id": best_node, "task": payload, "task_id": task_id}
    else:
        return {"status": "queued", "reason": "no suitable node", "task": payload, "task_id": task_id}

@app.get("/tasks/status/{task_id}", dependencies=[Depends(check_api_key)])
def get_task_status_api(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        return {}
    return {"status": task.status, "node_id": task.node_id, "result": task.result, "payload": task.payload}

@app.post("/tasks/result", dependencies=[Depends(check_api_key)])
def report_result(payload: dict = Body(...), db: Session = Depends(get_db)):
    node_id = payload.get('node_id')
    task_id = payload.get('task_id')
    result = payload.get('result')
    now = time.time()
    task = db.query(Task).filter_by(id=task_id).first()
    if task:
        task.status = 'done'
        task.result = result
        task.completed_at = now
        db.commit()
    return {"status": "result_received", "task_id": task_id}

@app.post("/tasks/reject", dependencies=[Depends(check_api_key)])
def reject_task(payload: dict = Body(...), db: Session = Depends(get_db)):
    task = payload.get('task')
    task_id = task.get('id')
    t = db.query(Task).filter_by(id=task_id).first()
    if t:
        t.status = 'queued'
        t.node_id = None
        db.commit()
    return {"status": "requeued", "task": task}

@app.get("/tasks/queued", dependencies=[Depends(check_api_key)])
def get_queued_tasks(db: Session = Depends(get_db)):
    now = time.time()
    timeout = 30
    queued = []
    for t in db.query(Task).filter_by(status='queued'):
        queued.append(t.payload)
    for t in db.query(Task).filter_by(status='assigned'):
        if now - (t.assigned_at or 0) > timeout:
            t.status = 'queued'
            t.node_id = None
            db.commit()
            queued.append(t.payload)
    return queued

@app.get("/tasks/in_progress", dependencies=[Depends(check_api_key)])
def get_in_progress_tasks(db: Session = Depends(get_db)):
    return {t.id: {"status": t.status, "node_id": t.node_id, "payload": t.payload} for t in db.query(Task).filter_by(status='assigned')}

@app.get("/tasks/results", dependencies=[Depends(check_api_key)])
def get_all_results(db: Session = Depends(get_db)):
    return {t.id: {"result": t.result, "node_id": t.node_id, "payload": t.payload} for t in db.query(Task).filter_by(status='done')}

faiss_db = SimpleFaissDB(dim=384)

@app.post("/vector_search", dependencies=[Depends(check_api_key)])
def vector_search(query: dict = Body(...)):
    vector = query.get('vector')
    k = query.get('k', 5)
    results = faiss_db.search(np.array(vector), k)
    return {"results": results}