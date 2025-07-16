# ReasoningAgent: Rust + Python + FastAPI

## Features
- Rust-based ReasoningAgent with OpenAI LLM plugin (retry, logging, config)
- Python FastAPI REST API: `/task`, `/result/{task_id}`, `/query`, `/metrics`, `/healthz`
- SQLite persistence for all tasks/answers
- API Key authentication for all endpoints
- Per-API-key rate limiting (default: 60/minute, configurable)
- Prometheus metrics endpoint for observability
- **Async LLM task queue with Celery + Redis**
- Dockerized for reproducibility and orchestration
- Ready for extension: OAuth2, async queue, Prometheus, etc.

## Quickstart (Docker Compose)

1. **docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     redis:
       image: redis:7
       ports:
         - "6379:6379"
     agent:
       build: .
       ports:
         - "8000:8000"
       environment:
         OPENAI_API_KEY: sk-...
         API_KEYS: key1,key2
         RATE_LIMIT: 60/minute
         REDIS_URL: redis://redis:6379/0
       depends_on:
         - redis
       command: uvicorn api.main:app --host 0.0.0.0 --port 8000
     worker:
       build: .
       environment:
         OPENAI_API_KEY: sk-...
         API_KEYS: key1,key2
         RATE_LIMIT: 60/minute
         REDIS_URL: redis://redis:6379/0
       depends_on:
         - redis
       command: celery -A api.worker worker --loglevel=info
   ```

2. **Start all services:**
   ```sh
   docker-compose up --build
   ```

3. **API Endpoints:**
   - `POST /task` — Submit a prompt, get a `task_id` (async)
   - `GET /result/{task_id}` — Poll for LLM answer/result
   - `GET /query` — Query previous answers
   - `GET /metrics` — Prometheus metrics endpoint
   - `GET /healthz` — Health check

## Async LLM Task Flow
- `/task` enqueues a background LLM job, returns a `task_id`
- `/result/{task_id}` lets you poll for the answer/status
- Celery worker runs LLM call and stores result in DB
- Scalable, robust, and non-blocking

## Best Practices
- Use Docker Compose for local dev and orchestration
- Use Redis for Celery broker and backend
- Run multiple workers for scale
- Use `/result/{task_id}` to poll for completion
- All endpoints require API key and are rate-limited
- Use Prometheus and Grafana for observability