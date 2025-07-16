# ReasoningAgent: Rust + Python + FastAPI

## Features
- Rust-based ReasoningAgent with OpenAI LLM plugin
- Python FastAPI REST API: `/task`, `/query`, `/metrics`
- Dockerized for reproducibility and orchestration
- Ready for extension: persistence, metrics, multi-LLM, etc.

## Quickstart (Docker)

1. **Build the Docker image:**
   ```sh
   docker build -t reasoning-agent .
   ```

2. **Run the container:**
   ```sh
   docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 reasoning-agent
   ```

3. **API Endpoints:**
   - `POST /task` — Submit a prompt, get LLM answer
   - `GET /metrics` — Health/metrics endpoint
   - `GET /query` — (To be implemented) Query previous answers

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

---

For more, see the code and comments in each file.