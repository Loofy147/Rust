# ReasoningAgent: Rust + Python + FastAPI

## Features
- Rust-based ReasoningAgent with OpenAI LLM plugin
- Python FastAPI REST API: `/task`, `/query`, `/metrics`
- Dockerized for reproducibility and orchestration
- Ready for extension: persistence, metrics, multi-LLM, etc.
- **API Key authentication for all endpoints**

## Quickstart (Docker)

1. **Build the Docker image:**
   ```sh
   docker build -t reasoning-agent .
   ```

2. **Run the container:**
   ```sh
   docker run -e OPENAI_API_KEY=sk-... -e API_KEYS=key1,key2 -p 8000:8000 reasoning-agent
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

---

For more, see the code and comments in each file.