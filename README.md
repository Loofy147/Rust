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

## REST API
- Start with `uvicorn api.rest:app --reload`
- See `/docs` for OpenAPI/Swagger UI