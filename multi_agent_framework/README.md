# Multi-Agent Cooperative Framework

## Features
- Knowledge Graph (NetworkX + spaCy)
- Vector Store (FAISS + Sentence Transformers)
- Modular, threaded agents (ingestion, processing, distribution, manager, webscraper, code generator, maintenance)
- Orchestrator with CLI and REST API (FastAPI)
- Distributed scaling prototype (multiprocessing/threading)
- External API integration (OpenAI, web scraping)
- Configurable, extensible, production-ready

## Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage
- Place a text file as `sample.txt` in the root.
- Run: `python orchestrator.py`
- REST API available at `http://localhost:8000` (see endpoints below)
- Extend agents for your ML/NLP pipelines, APIs, or workflows.

## REST API Endpoints
- `POST /submit_task` — Submit a task to an agent. JSON: `{ "agent": "webscraper", "msg": { ... } }`
- `GET /agent_status` — Get status of all agents.
- `GET /health` — Health check.

## Agents
- **IngestionAgent**: File/API ingestion
- **ProcessingAgent**: Embedding, KG update, hybrid search
- **DistributionAgent**: Routing, logging
- **ManagerAgent**: Orchestration, health checks
- **WebScraperAgent**: Scrapes web pages, sends text to processing
- **CodeGeneratorAgent**: Generates code using OpenAI API
- **MaintenanceAgent**: Monitors, restarts, cleans up

## Extending
- Add new agents in `agents/`
- Plug in new vector/graph backends in `core/`
- Add REST endpoints in `orchestrator.py` (see FastAPI docs)

## License
MIT