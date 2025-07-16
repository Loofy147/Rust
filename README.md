# Modular Agent System

## Features
- Pluggable algorithms (tokenizers, preprocessors)
- LLM API integration (OpenAI, HuggingFace, etc.)
- Persistent knowledge graph (KG) and vector storage
- REST API for external control and monitoring
- Supervisor and Metrics agents for resilience and observability
- Retry/backoff for fault tolerance

## Setup
```bash
pip install -r requirements.txt
```

## Configuration
Edit `config.yaml` for runtime, API keys, and plugin settings.

## Running
```bash
python main.py
```

## Extending
- Add plugins in `plugins/`
- Add storage backends in `storage/`
- Add new agents in `agents/`

## UI Dashboard
- Run: `streamlit run ui/dashboard.py`
- Features: health, data view, task submission

## gRPC API
- Proto: `protos/agent.proto`
- Server: `python api/grpc_server.py`

## Advanced Features
- Circuit breaker: see `utils/circuit_breaker.py`
- Hot-reload and Prometheus metrics: ready for extension

## REST API
- Start with `uvicorn api.rest:app --reload`
- See `/docs` for OpenAPI/Swagger UI