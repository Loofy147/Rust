import requests
import subprocess
import time
import sys

API_URL = "http://localhost:8000"  # Adjust as needed
MIN_NODES = 1
MAX_NODES = 5
SCALE_UP_QUEUE = 2  # If more than this many queued tasks, scale up
SCALE_DOWN_IDLE = 30  # Seconds a node must be idle to be killed

nodes = {}

while True:
    # Get node info
    nodes_info = requests.get(f"{API_URL}/agents/nodes").json()
    queued = requests.get(f"{API_URL}/tasks/queued").json()
    now = time.time()
    # Remove dead nodes from our tracking
    for nid in list(nodes.keys()):
        if nid not in nodes_info:
            nodes[nid].terminate()
            del nodes[nid]
    # Scale up if too many queued tasks and not at max nodes
    if len(queued) > SCALE_UP_QUEUE and len(nodes) < MAX_NODES:
        new_id = f"auto-node-{int(time.time())}"
        print(f"[AutoScaler] Launching new node: {new_id}")
        proc = subprocess.Popen([sys.executable, "distributed_node.py", new_id])
        nodes[new_id] = proc
    # Scale down if nodes are idle for too long and above min nodes
    for nid, info in nodes_info.items():
        if len(nodes) <= MIN_NODES:
            break
        last_seen = info.get('last_seen_delta', 0)
        load = info.get('load', 0)
        if load == 0 and last_seen < SCALE_DOWN_IDLE:
            print(f"[AutoScaler] Terminating idle node: {nid}")
            requests.post(f"{API_URL}/agents/deregister", json={"node_id": nid})
            if nid in nodes:
                nodes[nid].terminate()
                del nodes[nid]
    time.sleep(5)