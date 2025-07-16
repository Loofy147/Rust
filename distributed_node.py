import requests
import time
import random
import sys
import uuid
import signal

API_URL = "http://localhost:8000"  # Adjust as needed
NODE_ID = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())

# Example capabilities (could be dynamic)
CAPABILITIES = {"gpu": bool(random.getrandbits(1)), "vectorizer": True}

# Register node
r = requests.post(f"{API_URL}/agents/register", json={"node_id": NODE_ID})
print(f"Registered node: {NODE_ID} | {r.json()}")

current_load = 0

def heartbeat():
    global current_load
    r = requests.post(f"{API_URL}/agents/heartbeat", json={"node_id": NODE_ID, "capabilities": CAPABILITIES, "load": current_load})
    print(f"Heartbeat: {r.json()}")

def poll_tasks():
    r = requests.get(f"{API_URL}/tasks/poll/{NODE_ID}")
    return r.json().get('tasks', [])

def poll_queued_tasks():
    r = requests.get(f"{API_URL}/tasks/queued")
    return r.json()

def report_result(task_id, result):
    r = requests.post(f"{API_URL}/tasks/result", json={"node_id": NODE_ID, "task_id": task_id, "result": result})
    print(f"Reported result for {task_id}: {r.json()}")

def reject_task(task):
    r = requests.post(f"{API_URL}/tasks/reject", json={"task": task})
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
    # Simulate processing
    time.sleep(random.uniform(1, 3))
    result = f"Processed by {NODE_ID}: {task.get('text', '')}"
    report_result(task.get('id', str(uuid.uuid4())), result)
    current_load -= 1

def deregister():
    r = requests.post(f"{API_URL}/agents/deregister", json={"node_id": NODE_ID})
    print(f"Deregistered node: {NODE_ID} | {r.json()}")

if __name__ == "__main__":
    def handle_exit(signum, frame):
        deregister()
        exit(0)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    while True:
        heartbeat()
        tasks = poll_tasks()
        for task in tasks:
            process_task(task)
        # If idle, try to grab a queued task
        if not tasks:
            queued = poll_queued_tasks()
            for task in queued:
                if can_handle(task):
                    process_task(task)
                    queued.remove(task)
        time.sleep(2)