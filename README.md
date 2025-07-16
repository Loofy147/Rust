# Distributed, Auto-Scaling Agent System (DB-Backed)

## Overview
This system is a production-grade, distributed, auto-scaling agent platform with:
- **FastAPI** REST API
- **PostgreSQL** (via SQLAlchemy) for persistent state
- **Distributed nodes** (auto-register, heartbeat, deregister)
- **Auto-scaler** (launches/kills nodes based on load)
- **Streamlit dashboard** for live monitoring and control
- **Advanced task routing, load balancing, and recovery**

---

## Features
- **Persistent state:** All nodes, tasks, and results are stored in PostgreSQL
- **Auto-scaling:** Nodes are launched/killed based on system load and queue
- **Distributed nodes:** Each node registers, heartbeats, and processes tasks
- **Smart task routing:** Tasks are assigned to the best available node (capabilities, load)
- **Reliable delivery:** Tasks are retried/reassigned on failure or timeout
- **Live dashboard:** Monitor nodes, tasks, results, and system health

---

## File Structure
```
requirements.txt
config.yaml
migrate_db.py
/db/
  models.py
  session.py
/api/
  rest.py
/distributed_node.py
/auto_scaler.py
/ui/
  distributed_dashboard.py
```

---

## Setup

### 1. **Install PostgreSQL**
- Create a database (default: `agentsys`)
- Default connection: `postgresql://postgres:postgres@localhost:5432/agentsys`
- Set `DATABASE_URL` env var if using a different connection string

### 2. **Install dependencies**
```
pip install -r requirements.txt
```

### 3. **Run DB migration**
```
python migrate_db.py
```

### 4. **Start API server**
```
uvicorn api.rest:app --reload
```

### 5. **Start nodes**
```
python distributed_node.py node-1
python distributed_node.py node-2
# Or let the auto-scaler launch nodes
```

### 6. **Start auto-scaler**
```
python auto_scaler.py
```

### 7. **Start dashboard**
```
streamlit run ui/distributed_dashboard.py
```

---

## Usage

### **Submit a Task**
- Via dashboard or API (`/tasks/submit`)
- Example payload:
```json
{
  "text": "Process this data",
  "required": {"gpu": true}
}
```

### **Monitor System**
- Dashboard shows live nodes, queued/in-progress tasks, and results
- API endpoints:
  - `/agents/nodes` — List all nodes
  - `/tasks/queued` — Queued tasks
  - `/tasks/in_progress` — In-progress tasks
  - `/tasks/results` — Completed results

### **Scaling**
- Auto-scaler launches new nodes if load/queue is high
- Terminates idle nodes
- Nodes auto-register/deregister

### **Node Capabilities**
- Each node reports its capabilities (e.g., GPU, plugins)
- Tasks can require specific capabilities

### **Reliable Delivery & Recovery**
- Tasks are retried/reassigned if a node fails or times out
- At-least-once delivery

---

## Customization
- **Database:** Change `DATABASE_URL` in `db/session.py` or via env var
- **Scaling policies:** Edit thresholds in `auto_scaler.py`
- **Node logic:** Extend `distributed_node.py` for custom processing
- **API:** Extend `api/rest.py` for more endpoints or security

---

## Example: Add a New Task Type
1. Add logic in `distributed_node.py` to handle new task types
2. Submit tasks with a `type` field (e.g., `{ "type": "summarize", ... }`)
3. Route and process as needed

---

## Example: Add a New Node Capability
1. Add to `CAPABILITIES` in `distributed_node.py`
2. Submit tasks with `required` field (e.g., `{ "required": { "gpu": true } }`)
3. Only nodes with that capability will process the task

---

## Troubleshooting
- **DB connection errors:** Check `DATABASE_URL` and PostgreSQL status
- **Nodes not scaling:** Check auto-scaler logs and thresholds
- **Tasks not processed:** Ensure nodes are running and have required capabilities

---

## License
MIT