# ReasoningAgent

A modular, production-ready agent system with plugin interfaces for LLM, KG, vector store, and metrics. Includes REST API for task injection and status, and robust error handling.

## Features
- Pluggable LLM, KG, vector store, and metrics
- REST API (FastAPI) for task management
- Robust error handling and retries
- Persistence for KG and vectors
- Observability and metrics
- Secure API key authentication

## Setup
1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables in `.env` (see below)
4. Run the API:
   ```bash
   uvicorn api.main:app --reload
   ```

## Environment Variables
- `API_KEY`: API key for REST endpoints
- `OPENAI_API_KEY`: Your OpenAI API key
- `DB_URL`: Database URL for KG (e.g., `sqlite:///kg.db`)

## Testing
```bash
pytest
```

## Extending
- Implement new plugins by subclassing the interfaces in `agent/interfaces.py`.
- Add new endpoints or background processing as needed.