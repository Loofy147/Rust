# Async & Distributed Patterns

This document describes asynchronous agent usage, distributed patterns, and API stubs in the Super Advanced Agent Framework.

## Async Agents

### AsyncLLMAgent
- Provides async embedding, add, and search using asyncio and ThreadPoolExecutor.
- Use for high-throughput or concurrent scenarios.

**Example:**
```python
from async_llm_agent import AsyncLLMAgent, EmbeddingPipeline
import asyncio
store = FAISSVectorStore(dim=384)
embedder = EmbeddingPipeline()
agent = AsyncLLMAgent("AsyncDemo", store, embedder)

async def main():
    await agent.aadd_text_memory("Async: The Eiffel Tower is in Paris.")
    results = await agent.asearch_text("museum")
    print(results)
asyncio.run(main())
```

### AsyncLLMWrapper
- Wraps LLMGenerator for async text generation.

**Example:**
```python
from super_advanced_agents import LLMGenerator
from super_advanced_agents import AsyncLLMWrapper
llm = LLMGenerator()
async_llm = AsyncLLMWrapper(llm)
async def demo():
    result = await async_llm.agenerate("Say hello!", max_length=20)
    print(result)
```

## Distributed Patterns

### DistributedVectorStoreStub
- Example stub for a distributed vector store (could be REST/gRPC client).
- Replace with a real client for production.

**Example:**
```python
from super_advanced_agents import DistributedVectorStoreStub
store = FAISSVectorStore(dim=384)
dist_store = DistributedVectorStoreStub(store)
dist_store.add(...)
results = dist_store.search(...)
```

### Exposing Agents/Orchestrators via FastAPI
- Use FastAPI to expose agent/orchestrator endpoints for distributed or multi-process use.

**Example:**
```python
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search(req: QueryRequest):
    results = agent.search_text(req.query, top_k=req.top_k)
    return {"results": results}

# To run: uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Best Practices
- Use async agents for concurrent workloads or web APIs.
- For distributed setups, use REST/gRPC for communication between agents and orchestrators.
- Add authentication and rate limiting for production APIs.
- Use local caching to reduce latency for frequent queries.

## Extension Points
- Implement a full REST/gRPC client for distributed vector store or agent access.
- Add background workers for batch or scheduled tasks.
- Integrate with cloud deployment (Docker, Kubernetes, etc.).