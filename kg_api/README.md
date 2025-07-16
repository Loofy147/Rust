# KnowledgeGraphEngine API

A secure, async FastAPI service for advanced knowledge graph management and reasoning.

## Features
- Async CRUD for entities and relationships
- Advanced querying and reasoning
- JWT/API key authentication
- Rate limiting
- Prometheus metrics
- OpenAPI docs

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

### Query Entities
```bash
curl -X GET "http://localhost:8000/entities?type=CONCEPT&name=Test" \
  -H "Authorization: Bearer <JWT>"
```

### Reasoning Endpoint
```bash
curl -X GET "http://localhost:8000/reasoning?query=..." \
  -H "Authorization: Bearer <JWT>"
```

## Metrics
- Prometheus metrics available at `/metrics`

## Tracing
- OpenTelemetry tracing enabled if `OTEL_ENABLED=1` in the environment

---

For more, see the OpenAPI docs at `/docs` or `/openapi.json`.