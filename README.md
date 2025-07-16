# ReasoningAgent: Rust + Python + FastAPI

## Features
- Rust-based ReasoningAgent with OpenAI LLM plugin (retry, logging, config)
- Python FastAPI REST API: `/task`, `/query`, `/metrics`, `/healthz`
- SQLite persistence for all tasks/answers
- API Key authentication for all endpoints
- Per-API-key rate limiting (default: 60/minute, configurable)
- Dockerized for reproducibility and orchestration
- Ready for extension: OAuth2, async queue, Prometheus, etc.

## Quickstart (Docker)

1. **Build the Docker image:**
   ```sh
   docker build -t reasoning-agent .
   ```

2. **Run the container:**
   ```sh
   docker run -e OPENAI_API_KEY=sk-... -e API_KEYS=key1,key2 -e RATE_LIMIT=60/minute -p 8000:8000 reasoning-agent
   ```

3. **API Endpoints:**
   - `POST /task` — Submit a prompt, get LLM answer
   - `GET /query` — Query previous answers
   - `GET /metrics` — Health/metrics endpoint
   - `GET /healthz` — Health check

## Authentication

All endpoints require an API key via the `X-API-Key` header.
- Set valid keys in the `API_KEYS` env var (comma-separated).
- Example: `-e API_KEYS=key1,key2`
- Example request:
  ```sh
  curl -X POST http://localhost:8000/task \
    -H "X-API-Key: key1" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Hello, world!"}'
  ```

## Rate Limiting
- Per-API-key, default 60/minute (configurable via `RATE_LIMIT` env var)
- Returns HTTP 429 if exceeded
- Example: `-e RATE_LIMIT=100/hour`

## Persistence
- All tasks and answers are stored in SQLite (`reasoning_agent.db` by default)
- Change DB location with `DATABASE_URL` env var

## Orchestration
- **Docker Compose:**
  - Add Redis for distributed rate limiting if needed
  - Example `docker-compose.yml`:
    ```yaml
    version: '3.8'
    services:
      agent:
        build: .
        ports:
          - "8000:8000"
        environment:
          OPENAI_API_KEY: sk-...
          API_KEYS: key1,key2
          RATE_LIMIT: 60/minute
    ```
- **Kubernetes:**
  - Use a `Deployment` and `Service` manifest
  - Mount secrets for API keys and OpenAI key

## CI/CD
- GitHub Actions workflow in `.github/workflows/ci.yml` builds, tests, and checks Docker image

## Extending
- Add OAuth2, async queue, Prometheus, or swap DB as needed
- See code comments for extension points

## Best Practices
- Never log or expose API keys
- Use environment variables for all secrets/config
- Use Docker for reproducibility
- Use per-API-key rate limiting to control costs
- Use CI/CD for all changes