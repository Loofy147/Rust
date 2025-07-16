import requests
import time
import random
import sys
import uuid
import signal
import os
from dotenv import load_dotenv
import openai
from sentence_transformers import SentenceTransformer
from vector_db import SimpleFaissDB

load_dotenv()
API_KEY = os.environ.get('API_KEY', 'changeme')
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

API_URL = "http://localhost:8000"  # Adjust as needed
NODE_ID = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
CAPABILITIES = {"gpu": bool(random.getrandbits(1)), "vectorizer": True}
current_load = 0

vectorizer = SentenceTransformer('all-MiniLM-L6-v2')
faiss_db = SimpleFaissDB(dim=384)

def register():
    r = requests.post(f"{API_URL}/agents/register", json={"node_id": NODE_ID}, headers=HEADERS)
    print(f"Registered node: {NODE_ID} | {r.json()}")

def heartbeat():
    global current_load
    r = requests.post(f"{API_URL}/agents/heartbeat", json={"node_id": NODE_ID, "capabilities": CAPABILITIES, "load": current_load}, headers=HEADERS)
    print(f"Heartbeat: {r.json()}")

def deregister():
    r = requests.post(f"{API_URL}/agents/deregister", json={"node_id": NODE_ID}, headers=HEADERS)
    print(f"Deregistered node: {NODE_ID} | {r.json()}")

def poll_queued_tasks():
    r = requests.get(f"{API_URL}/tasks/queued", headers=HEADERS)
    return r.json()

def get_in_progress():
    r = requests.get(f"{API_URL}/tasks/in_progress", headers=HEADERS).json()
    return r

def report_result(task_id, result):
    r = requests.post(f"{API_URL}/tasks/result", json={"node_id": NODE_ID, "task_id": task_id, "result": result}, headers=HEADERS)
    print(f"Reported result for {task_id}: {r.json()}")

def reject_task(task):
    r = requests.post(f"{API_URL}/tasks/reject", json={"task": task}, headers=HEADERS)
    print(f"Rejected task: {task}")

def can_handle(task):
    required = task.get('required', {})
    for k, v in required.items():
        if CAPABILITIES.get(k) != v:
            return False
    return True

def process_task(task):
    global current_load
    if not can_handle(task):
        reject_task(task)
        return
    print(f"Processing task: {task}")
    current_load += 1
    result = None
    if task.get('type') == 'llm' and OPENAI_API_KEY:
        prompt = task.get('text', '')
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = resp['choices'][0]['message']['content']
        except Exception as e:
            result = f"LLM error: {e}"
    elif task.get('type') == 'vector':
        text = task.get('text', '')
        vector = vectorizer.encode([text])[0]
        faiss_db.upsert(task.get('id', str(uuid.uuid4())), vector, payload=text)
        # Optionally perform a search
        search_results = faiss_db.search(vector, k=3)
        result = {'vector': vector.tolist(), 'search_results': search_results}
    else:
        time.sleep(random.uniform(1, 3))
        result = f"Processed by {NODE_ID}: {task.get('text', '')}"
    report_result(task.get('id', str(uuid.uuid4())), result)
    current_load -= 1

def main():
    register()
    def handle_exit(signum, frame):
        deregister()
        exit(0)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    while True:
        heartbeat()
        queued = poll_queued_tasks()
        for task in queued:
            if can_handle(task):
                process_task(task)
                queued.remove(task)
        time.sleep(2)

if __name__ == "__main__":
    main()