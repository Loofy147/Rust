# Multi-Agent Cooperative Framework (Advanced Distributed)

## Features
- Knowledge Graph (NetworkX, spaCy, Neo4j)
- Vector Store (FAISS, Elasticsearch, Sentence Transformers)
- Modular, threaded, and distributed agents (Ray, Celery)
- Orchestrator with CLI, REST API (FastAPI), Ray, and Celery support
- Distributed scaling (Ray, Celery, Redis)
- External API integration (OpenAI, HuggingFace, LangChain, Slack, etc.)
- Advanced agent types: Summarization, Translation, Notification, Audit
- Agent heartbeats, health checks, dynamic scaling, and pluggable pipelines
- Centralized logging, tracing, and compliance

## Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# For Celery: start Redis server (default: redis-server)
# For Ray: ray start --head
```

## Usage
- Place a text file as `sample.txt` in the root.
- Run: `python orchestrator.py` (threaded/REST mode)
- Run: `python distributed/ray_orchestrator.py` (Ray distributed mode)
- Run: `celery -A distributed.celery_base.celery_app worker --loglevel=info` (Celery distributed mode)
- REST API available at `http://localhost:8000`

## Distributed Orchestrators
- **Ray**: Launches Ray agents as distributed actors, supports dynamic scaling, health checks, and message passing.
- **Celery**: Launches Celery agents as distributed tasks, supports robust queueing, retries, and monitoring (Flower).

## Integrations
- **Elasticsearch**: Distributed vector/text search (`integrations/elasticsearch_store.py`)
- **Neo4j**: Persistent, queryable knowledge graph (`integrations/neo4j_kg.py`)
- **LangChain**: Advanced LLM orchestration and chaining
- **OpenAI/HuggingFace**: LLMs for summarization, translation, codegen, etc.

## Advanced Practices
- Agent heartbeats, health checks, and auto-recovery
- Dynamic agent scaling (Ray/Celery)
- Task prioritization and scheduling
- Distributed logging and tracing
- Pluggable agent registry and pipelines
- Secure API key management (env vars, secret managers)
- Graceful shutdown and restart

## Agents
- **IngestionAgent**: File/API ingestion
- **ProcessingAgent**: Embedding, KG update, hybrid search
- **DistributionAgent**: Routing, logging
- **ManagerAgent**: Orchestration, health checks
- **WebScraperAgent**: Scrapes web pages, sends text to processing
- **CodeGeneratorAgent**: Generates code using OpenAI API
- **MaintenanceAgent**: Monitors, restarts, cleans up
- **SummarizationAgent**: Summarizes text (Ray & Celery)
- **TranslationAgent**: Translates text (Ray & Celery)
- **NotificationAgent**: Sends notifications (Ray & Celery)
- **AuditAgent**: Audits and logs agent actions (Ray & Celery)

## Extending
- Add new agents in `agents/`
- Plug in new vector/graph backends in `core/` or `integrations/`
- Add REST endpoints in `orchestrator.py` (see FastAPI docs)
- Register new agent types in Ray/Celery orchestrators

## License
MIT