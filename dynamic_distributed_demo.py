import requests
import threading
import time
import random
import yaml

# --- CONFIG ---
with open('config.yaml') as f:
    config = yaml.safe_load(f)
API_URL = f"http://{config['api']['host']}:{config['api']['port']}"
AUTH = {"Authorization": f"Bearer {config['api']['auth_token']}"}

# --- DYNAMIC PLUGIN MANAGEMENT ---
def list_plugins():
    r = requests.get(f"{API_URL}/plugins", headers=AUTH)
    print("Current plugins:", r.json())

def load_plugin(module, cls):
    r = requests.post(f"{API_URL}/plugins/load", headers=AUTH, json={"module": module, "class": cls})
    print(f"Loaded plugin {cls}: {r.json()}")

def unload_plugin(cls):
    r = requests.post(f"{API_URL}/plugins/unload", headers=AUTH, json={"class": cls})
    print(f"Unloaded plugin {cls}: {r.json()}")

# --- DISTRIBUTED NODE SIMULATION ---
class AgentNode(threading.Thread):
    def __init__(self, node_id):
        super().__init__()
        self.node_id = node_id
        self.running = True
        self.status = 'idle'
    def register(self):
        # Simulate registration (could POST to /agents in a real distributed setup)
        print(f"Node {self.node_id} registered.")
    def heartbeat(self):
        # Simulate heartbeat (could PATCH/POST to /agents/{id}/heartbeat)
        print(f"Node {self.node_id} heartbeat. Status: {self.status}")
    def process_task(self, task):
        self.status = 'processing'
        print(f"Node {self.node_id} processing: {task}")
        time.sleep(random.uniform(0.5, 2.0))
        self.status = 'idle'
    def run(self):
        self.register()
        while self.running:
            self.heartbeat()
            time.sleep(2)

# --- TASK DISTRIBUTION ---
def submit_task_to_node(node_id, text, priority=10):
    payload = {"type": "process", "text": text, "priority": priority, "node_id": node_id}
    r = requests.post(f"{API_URL}/tasks", headers=AUTH, json=payload)
    print(f"Submitted task to node {node_id}: {r.json()}")
    return r.json().get('task_id')

def get_task_status(task_id):
    r = requests.get(f"{API_URL}/tasks/{task_id}", headers=AUTH)
    print(f"Task {task_id} status: {r.json()}")
    return r.json()

# --- MAIN DEMO ---
if __name__ == "__main__":
    # 1. Dynamic plugin management
    list_plugins()
    load_plugin("plugins.normalizer_plugin", "NormalizerPlugin")
    list_plugins()
    unload_plugin("NormalizerPlugin")
    list_plugins()

    # 2. Simulate distributed nodes
    nodes = [AgentNode(i) for i in range(3)]
    for node in nodes:
        node.start()

    # 3. Distribute tasks round-robin
    texts = [
        "Distributed systems are powerful.",
        "Multi-node orchestration is scalable.",
        "Dynamic plugin loading is flexible."
    ]
    task_ids = []
    for i, text in enumerate(texts):
        node_id = i % len(nodes)
        task_id = submit_task_to_node(node_id, text, priority=random.randint(1, 10))
        task_ids.append(task_id)

    # 4. Query task status
    time.sleep(3)
    for task_id in task_ids:
        get_task_status(task_id)

    # 5. Stop nodes after demo
    for node in nodes:
        node.running = False
    for node in nodes:
        node.join()
    print("Demo complete.")