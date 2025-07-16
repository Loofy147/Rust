# Multi-Agent Cooperative Framework

## Features
- Knowledge Graph (NetworkX + spaCy)
- Vector Store (FAISS + Sentence Transformers)
- Modular, threaded agents (ingestion, processing, distribution, manager)
- Orchestrator with CLI/REST API hooks
- Configurable, extensible, production-ready

## Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage
- Place a text file as `sample.txt` in the root.
- Run: `python orchestrator.py`
- Extend agents for your ML/NLP pipelines, APIs, or workflows.

## Extending
- Add new agents in `agents/`
- Plug in new vector/graph backends in `core/`
- Add REST endpoints in `orchestrator.py` (see FastAPI docs)

## License
MIT