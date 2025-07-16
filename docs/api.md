# API Reference

## REST Endpoints

### `POST /tasks`
Submit a new task for processing.

**Request Body:**
```json
{
  "input": "your task input"
}
```

**Response:**
```json
{
  "id": "task-id",
  "status": "pending|completed|failed",
  "result": "..."
}
```

**Headers:**
- `x-api-key`: Your API key

**Example:**
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "x-api-key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "your task input"}'
```

---

### `GET /tasks/{task_id}`
Get the status and result of a task.

**Response:**
```json
{
  "id": "task-id",
  "status": "pending|completed|failed",
  "result": "..."
}
```

**Headers:**
- `x-api-key`: Your API key

**Example:**
```bash
curl -X GET "http://localhost:8000/tasks/{task_id}" \
  -H "x-api-key: your-secret-key"
```

---

### `GET /metrics`
Prometheus metrics endpoint for monitoring.

**Example:**
```bash
curl http://localhost:8000/metrics
```

---

## WebSocket Endpoints

### `/ws/tasks/{task_id}`
Subscribe to live updates for a task.

**Messages:**
```json
{
  "status": "pending|completed|failed",
  "result": "..."
}
```

**Example (Python):**
```python
import websockets
import asyncio

async def listen(task_id):
    uri = f"ws://localhost:8000/ws/tasks/{task_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            msg = await websocket.recv()
            print(msg)

asyncio.run(listen("your-task-id"))
```

---

## Authentication
All endpoints require an API key via the `x-api-key` header.

---

## OpenAPI/Swagger
Interactive API docs are available at `/docs` when running the API.

**To view the full OpenAPI schema:**
- Visit [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- Or use:
  ```bash
  curl http://localhost:8000/openapi.json
  ```