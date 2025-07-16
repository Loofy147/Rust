# KnowledgeGraphEngine API

A secure, async FastAPI service for advanced knowledge graph management and reasoning.

## Features
- Async CRUD for entities and relationships
- Advanced querying and reasoning
- JWT/API key authentication
- Rate limiting
- Prometheus metrics
- OpenAPI docs
- Admin endpoints (health, stats, reload, export/import)

## Getting Started

### 1. Install dependencies
```bash
pip install fastapi aiosqlite uvicorn slowapi prometheus_fastapi_instrumentator pydantic
```

### 2. Run the API
```bash
uvicorn kg_api.main:app --reload
```

### 3. Authentication
- Obtain a JWT via `/token` (username: `admin`, password: `adminpass` by default)
- Or use an API key via the `x-api-key` header

### 4. OpenAPI Docs
- Visit [http://localhost:8000/docs](http://localhost:8000/docs)

## Example Requests

### Get JWT Token
```bash
curl -X POST http://localhost:8000/token -d "username=admin&password=adminpass"
```

### Add Entity
```bash
curl -X POST http://localhost:8000/entities \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"type": "CONCEPT", "name": "Test Entity", "properties": {"foo": "bar"}}'
```

### Get Entity
```bash
curl -X GET http://localhost:8000/entities/<entity_id> \
  -H "Authorization: Bearer <JWT>"
```

### Add Relationship
```bash
curl -X POST http://localhost:8000/relationships \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"source_id": "...", "target_id": "...", "type": "DEPENDS_ON"}'
```

### Query Entities (with Pagination/Filtering)
```bash
curl -X GET "http://localhost:8000/entities?type=CONCEPT&name=Test&limit=10&offset=0" \
  -H "Authorization: Bearer <JWT>"
```

### Reasoning with Context and Trace
```bash
curl -X GET "http://localhost:8000/reasoning?query=explain+decision&trace=1" \
  -H "Authorization: Bearer <JWT>"
```

### Error Handling Example (Invalid Entity)
```bash
curl -X GET http://localhost:8000/entities/invalid_id \
  -H "Authorization: Bearer <JWT>"
# Response: {"error": {"code": 404, "message": "Entity not found"}}
```

### Rate Limit Example
```bash
# Exceeding rate limit returns 429
curl -X GET http://localhost:8000/entities/<entity_id> \
  -H "Authorization: Bearer <JWT>"
# Response: {"error": {"code": 429, "message": "Rate limit exceeded"}}
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Stats
```bash
curl http://localhost:8000/stats
```

## Python Client Example
```python
import requests

API = "http://localhost:8000"
# Login
resp = requests.post(f"{API}/token", data={"username": "admin", "password": "adminpass"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
# Add entity
entity = {"type": "CONCEPT", "name": "PyClient", "properties": {}}
resp = requests.post(f"{API}/entities", json=entity, headers=headers)
eid = resp.json()["id"]
# Get entity
resp = requests.get(f"{API}/entities/{eid}", headers=headers)
print(resp.json())
```

## Metrics
- Prometheus metrics available at `/metrics`

## Tracing
- OpenTelemetry tracing enabled if `OTEL_ENABLED=1` in the environment

---

For more, see the OpenAPI docs at `/docs` or `/openapi.json`.