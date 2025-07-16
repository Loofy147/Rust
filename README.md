# ReasoningAgent: Rust + Python + FastAPI

## Features
- Rust-based ReasoningAgent with OpenAI LLM plugin
- Python FastAPI REST API: `/task`, `/query`, `/metrics`
- Dockerized for reproducibility and orchestration
- Ready for extension: persistence, metrics, multi-LLM, etc.
- **API Key authentication for all endpoints**
- **Per-API-key rate limiting (default: 60/minute)**

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
   - `GET /metrics` — Health/metrics endpoint
   - `GET /query` — Query previous answers

## Authentication

All endpoints require an API key via the `X-API-Key` header.

- Set valid keys in the `API_KEYS` environment variable (comma-separated).
- Example: `API_KEYS=key1,key2,key3`
- Example request:
  ```sh
  curl -X POST http://localhost:8000/task \
    -H 'X-API-Key: key1' \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "Hello, world!"}'
  ```

## Rate Limiting

All endpoints are rate-limited per API key (default: 60 requests per minute).

- Configure with the `RATE_LIMIT` environment variable (e.g., `RATE_LIMIT=100/hour`).
- Exceeding the limit returns HTTP 429 with a clear error message and headers:
  ```
  HTTP/1.1 429 Too Many Requests
  x-ratelimit-limit: 60
  x-ratelimit-remaining: 0
  x-ratelimit-reset: 60
  ```
- For distributed/multi-instance deployments, use Redis as a backend (see slowapi docs).

## Local Development (Advanced)
- Use `pyenv` to install Python 3.12
- Use `maturin develop` to build the Rust extension
- Run FastAPI with `uvicorn api.main:app --reload`

## Orchestration
- Healthcheck endpoint for Docker/Kubernetes
- Ready for Docker Compose or K8s manifests

## Extending
- Add persistence (SQLite, Postgres, etc.)
- Add Prometheus metrics
- Add more LLM providers or plugins

## Environment Variables
- `OPENAI_API_KEY` — Required for OpenAI LLM plugin
- `API_KEYS` — Comma-separated list of valid API keys
- `RATE_LIMIT` — Rate limit per API key (e.g., `60/minute`, `100/hour`)

---

For more, see the code and comments in each file.