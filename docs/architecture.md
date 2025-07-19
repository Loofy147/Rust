# Architecture

```mermaid
graph TD
    A[REST API (FastAPI)] -->|Task| B[ReasoningAgent Core]
    B -->|Query| C[KG Plugin]
    B -->|Vector Search| D[Vector Store Plugin]
    B -->|Prompt| E[Prompt Builder]
    B -->|LLM Call| F[LLM Plugin]
    B -->|Emit| G[Metrics Plugin]
    B -->|Store| C
    A -->|WebSocket| H[Client]
    G -->|/metrics| I[Prometheus]
```

- **Plugins**: Swappable for LLM, KG, Vector, Metrics
- **WebSocket**: For live task updates
- **Prometheus**: For metrics scraping
- **Dockerized**: For easy deployment

## Task Flow
1. Task submitted via REST
2. ReasoningAgent queries KG/vector store
3. Prompt is built and sent to LLM
4. Answer is stored in KG, metrics emitted
5. Status updates sent via WebSocket