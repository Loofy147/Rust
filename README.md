# Distributed Modular AI Orchestration Platform

## Overview

A production-grade, distributed, multi-tenant orchestration platform for AI/ML tasks, supporting modular agents, dynamic plugin management, robust vector/matrix operations, secure API access (OAuth2/JWT), and seamless integration with external AI tools (OpenAI, HuggingFace, Pinecone, etc.).

---

## Features

- **Distributed, Load-Aware Orchestration**: Auto-scaling, load balancing, node health checks, and speedy recovery.
- **Modular Agents**: Supervisor, Metrics, Processor, TaskQueue, Registry, Scheduler, Dynamic Plugin Loader.
- **Pluggable Plugins**: Tokenizer, Normalizer, Vectorizer, custom plugins via dynamic loader.
- **Vector DB Support**: FAISS, Pinecone, Milvus-ready, with unified vector search API.
- **Persistent Storage**: PostgreSQL (SQLAlchemy), Redis queue, file storage, vector DB.
- **Unified API**: FastAPI REST, gRPC, health, metrics, plugin management, vector search.
- **Security**: OAuth2/JWT authentication, API key fallback, multi-tenant support.
- **External AI Tool Integration**: OpenAI, HuggingFace, Pinecone, extensible adapters.
- **Observability**: Prometheus metrics, structured logging, heartbeat, circuit breaker.
- **UI Dashboard**: Streamlit dashboard for monitoring and management.
- **Cloud-Native Deployment**: Docker Compose, Kubernetes manifests, CI/CD ready.

---

## Architecture

```
+-------------------+      +-------------------+      +-------------------+
|   API Layer       |<---->|   Orchestrator    |<---->|   Agents/Plugins  |
| (FastAPI/gRPC/UI) |      | (Supervisor, ... )|      | (Vectorizer, ... )|
+-------------------+      +-------------------+      +-------------------+
        |                        |                        |
        v                        v                        v
+-------------------+      +-------------------+      +-------------------+
|   Storage Layer   |<---->|   Queue Layer     |<---->|   Vector DB       |
| (Postgres, Redis) |      | (Redis, ... )     |      | (FAISS, Pinecone) |
+-------------------+      +-------------------+      +-------------------+
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd <repo-dir>
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml` for DB, vector DB, plugin, and security settings.

### 3. Run Services

#### Local (dev):
```bash
uvicorn main:app --reload
streamlit run dashboard/app.py
```

#### Docker Compose:
```bash
docker-compose up --build
```

#### Kubernetes:
```bash
kubectl apply -f k8s/
```

---

## Configuration

Edit `config.yaml`:
- **database**: PostgreSQL DSN
- **redis**: Redis URL
- **vector_db**: FAISS/Pinecone/Milvus config
- **plugins**: Enable/disable, dynamic loading
- **security**: JWT secret, OAuth2, API keys
- **scaling**: Min/max nodes, cooldown, thresholds

---

## API Reference

### Authentication
- **/login**: Obtain JWT (OAuth2 password flow)
- **Bearer token** required for all endpoints

### Core Endpoints
- **/tasks/submit**: Submit AI/ML task
- **/tasks/{id}/status**: Get task status
- **/tasks/{id}/result**: Get task result
- **/vector/search**: Vector search (text/query vector)
- **/plugins/list**: List available plugins
- **/plugins/load**: Dynamically load plugin
- **/agents/registry**: List registered agents/nodes
- **/metrics**: Prometheus metrics
- **/health**: Health check
- **/external/ai**: Unified external AI tool access

### Example: Submit Task
```bash
curl -X POST /tasks/submit \
  -H "Authorization: Bearer <token>" \
  -d '{"type": "vectorize", "payload": {"text": "hello world"}}'
```

---

## Security

- **OAuth2/JWT**: Secure all endpoints, multi-tenant support
- **API Key**: Fallback for legacy clients
- **RBAC**: Role-based access for admin/user
- **TLS**: Use HTTPS in production
- **Secrets**: Store secrets in env vars or secret manager

---

## Deployment

### Docker Compose
- `docker-compose up --build`
- Services: API, Redis, Postgres, Vector DB, Dashboard

### Kubernetes
- `kubectl apply -f k8s/`
- Includes secrets, config, persistent volumes

### CI/CD
- Example GitHub Actions workflow in `.github/workflows/`
- Lint, test, build, deploy

---

## Monitoring & Observability

- **Prometheus**: `/metrics` endpoint
- **Grafana**: Import dashboards for metrics
- **Structured Logging**: JSON logs, log levels
- **Heartbeat**: Node health, auto-recovery
- **Circuit Breaker**: Prevent cascading failures

---

## Extending the System

- **Add Plugins**: Drop new plugin in `plugins/`, register in config or load dynamically
- **Add Agents**: Implement agent class, register in registry
- **Add External AI Tool**: Implement adapter, register with `ExternalAIToolAgent`
- **Custom Vector DB**: Implement `BaseVectorDB` interface

---

## Troubleshooting

- **Auth errors**: Check JWT/OAuth2 config, token expiry
- **DB errors**: Check Postgres/Redis connectivity, migrations
- **Vector search issues**: Check vector DB config, plugin status
- **Scaling issues**: Check auto-scaler logs, node health
- **Plugin errors**: Check plugin logs, dependencies

---

## File Structure

```
.
├── main.py
├── config.yaml
├── requirements.txt
├── README.md
├── agents/
│   ├── supervisor.py
│   ├── metrics.py
│   ├── processor.py
│   ├── task_queue.py
│   ├── registry.py
│   ├── scheduler.py
│   └── dynamic_loader.py
├── plugins/
│   ├── manager.py
│   ├── tokenizer.py
│   ├── normalizer.py
│   ├── vectorizer.py
│   └── ...
├── storage/
│   ├── base.py
│   ├── file.py
│   ├── vector_db.py
│   └── models.py
├── api/
│   ├── rest.py
│   ├── grpc.py
│   ├── health.py
│   ├── vector_search.py
│   └── external_ai.py
├── utils/
│   ├── retry.py
│   ├── logging.py
│   ├── circuit_breaker.py
│   ├── heartbeat.py
│   └── ...
├── dashboard/
│   └── app.py
├── queue/
│   └── redis_queue.py
├── external/
│   └── ai_tool_agent.py
├── k8s/
│   └── ...
└── .github/
    └── workflows/
```

---

## License

MIT License. See `LICENSE` file.

---

## Contact & Support

- [Your Name/Org]
- [Contact Email]
- [Issue Tracker/GitHub]