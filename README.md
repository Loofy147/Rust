# Super Advanced Agent Framework

This project is a modular, extensible framework for building, orchestrating, and collaborating with advanced AI agents powered by vector search, LLMs, multi-modal memory, and more.

## Features
- FAISS-based vector store with advanced retrieval
- Multiple agent types: Retriever, Summarizer, Conversational, Plugin, Personalization, Provenance, Expiry, Hybrid, Multi-modal
- LLM-based generation, re-ranking, and critique
- Context windowing, memory chunking, expiry, prioritization
- Plugin/tool integration
- Distributed and async support
- Orchestration: routing, chaining, fallback, supervision, collaboration, voting, consensus

## Quick Start
1. **Install dependencies:**
   ```bash
   pip install faiss-cpu torch transformers sentence-transformers pillow
   # For multi-modal: pip install git+https://github.com/openai/CLIP.git
   ```
2. **Run a demo:**
   ```bash
   python super_advanced_agents.py
   python orchestrator_demo.py
   python collaboration_orchestrator.py
   ```

## Documentation
- [Agents](docs/AGENTS.md)
- [Vector Store](docs/VECTOR_STORE.md)
- [Orchestration](docs/ORCHESTRATION.md)
- [Collaboration & Voting](docs/COLLABORATION.md)
- [Async & Distributed](docs/ASYNC_DISTRIBUTED.md)
- [Extending the Framework](docs/EXTENDING.md)

## Directory Structure
- `super_advanced_agents.py` — All advanced agent types and features
- `orchestrator_demo.py` — Orchestration patterns and demo
- `collaboration_orchestrator.py` — Agent collaboration, voting, and consensus
- `faiss_vector_store.py` — Vector store implementation
- `llm_agent.py`, `async_llm_agent.py`, `advanced_agents.py` — Specialized agent demos
- `docs/` — Detailed documentation for each component

## License
MIT