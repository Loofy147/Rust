import requests
import subprocess
import time
import sys

API_URL = "http://localhost:8000"  # Adjust as needed
MIN_NODES = 1
MAX_NODES = 5
SCALE_UP_QUEUE = 2  # If more than this many queued tasks, scale up
SCALE_UP_LOAD = 0.7  # If avg load > this, scale up
SCALE_DOWN_IDLE = 30  # Seconds a node must be idle to be killed
COOLDOWN = 20  # Seconds between scaling actions

nodes = {}
last_scale_action = 0

while True:
    nodes_info = requests.get(f"{API_URL}/agents/nodes").json()
    queued = requests.get(f"{API_URL}/tasks/queued").json()
    in_progress = requests.get(f"{API_URL}/tasks/in_progress").json()
    now = time.time()
    # Remove dead nodes from our tracking
    for nid in list(nodes.keys()):
        if nid not in nodes_info:
            nodes[nid].terminate()
            del nodes[nid]
    # Calculate average load
    loads = [info.get('load', 0) for info in nodes_info.values()]
    avg_load = sum(loads) / len(loads) if loads else 0
    # Scale up if needed
    if (len(queued) > SCALE_UP_QUEUE or avg_load > SCALE_UP_LOAD) and len(nodes) < MAX_NODES and now - last_scale_action > COOLDOWN:
        new_id = f"auto-node-{int(time.time())}"
        print(f"[AutoScaler] Launching new node: {new_id}")
        proc = subprocess.Popen([sys.executable, "distributed_node.py", new_id])
        nodes[new_id] = proc
        last_scale_action = now
    # Scale down if nodes are idle for too long and above min nodes
    for nid, info in nodes_info.items():
        if len(nodes) <= MIN_NODES:
            break
        last_seen = info.get('last_seen_delta', 0)
        load = info.get('load', 0)
        if load == 0 and last_seen < SCALE_DOWN_IDLE and now - last_scale_action > COOLDOWN:
            print(f"[AutoScaler] Terminating idle node: {nid}")
            requests.post(f"{API_URL}/agents/deregister", json={"node_id": nid})
            if nid in nodes:
                nodes[nid].terminate()
                del nodes[nid]
            last_scale_action = now
    print(f"[AutoScaler] Nodes: {len(nodes)} | Avg load: {avg_load:.2f} | Queued: {len(queued)} | In progress: {len(in_progress)}")
    time.sleep(5)