import requests
import time
import random
import sys
import uuid

API_URL = "http://localhost:8000"  # Adjust as needed
NODE_ID = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())

# Register node
r = requests.post(f"{API_URL}/agents/register", json={"node_id": NODE_ID})
print(f"Registered node: {NODE_ID} | {r.json()}")

def heartbeat():
    r = requests.post(f"{API_URL}/agents/heartbeat", json={"node_id": NODE_ID})
    print(f"Heartbeat: {r.json()}")

def poll_tasks():
    r = requests.get(f"{API_URL}/tasks/poll/{NODE_ID}")
    return r.json().get('tasks', [])

def report_result(task_id, result):
    r = requests.post(f"{API_URL}/tasks/result", json={"node_id": NODE_ID, "task_id": task_id, "result": result})
    print(f"Reported result for {task_id}: {r.json()}")

def process_task(task):
    print(f"Processing task: {task}")
    # Simulate processing
    time.sleep(random.uniform(1, 3))
    result = f"Processed by {NODE_ID}: {task.get('text', '')}"
    report_result(task.get('id', str(uuid.uuid4())), result)

if __name__ == "__main__":
    while True:
        heartbeat()
        tasks = poll_tasks()
        for task in tasks:
            process_task(task)
        time.sleep(2)