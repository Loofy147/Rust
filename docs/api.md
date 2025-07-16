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

---

### `GET /metrics`
Prometheus metrics endpoint for monitoring.

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

---

## Authentication
All endpoints require an API key via the `x-api-key` header.

---

## OpenAPI/Swagger
Interactive API docs are available at `/docs` when running the API.