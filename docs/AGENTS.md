# Agent Types

This document describes all agent types available in the Super Advanced Agent Framework.

## RetrieverAgent
- **Purpose:** Advanced retrieval, hybrid search, LLM-based re-ranking.
- **Key Methods:**
  - `retrieve(query_text, top_k=5, keyword=None, memory_type=None)`
  - `rerank_with_llm(query_text, results)`
- **Usage:**
  ```python
  agent = RetrieverAgent("Retriever", store, embedder, llm)
  results = agent.retrieve("museum", top_k=3, keyword="Louvre")
  reranked = agent.rerank_with_llm("museum", results)
  ```

## SummarizerAgent
- **Purpose:** Summarizes batches of retrieved memories using the LLM.
- **Key Methods:**
  - `summarize_memories(query_text, top_k=5, memory_type=None)`
- **Usage:**
  ```python
  agent = SummarizerAgent("Summarizer", store, embedder, llm)
  summary = agent.summarize_memories("Paris", top_k=3)
  ```

## ConversationalAgent
- **Purpose:** Maintains dialogue history, retrieves context, generates responses with LLM.
- **Key Methods:**
  - `add_turn(user_text, agent_text, turn_id=None)`
  - `get_context(query_text, top_k=3)`
  - `chat(user_text)`
- **Usage:**
  ```python
  agent = ConversationalAgent("Chatty", store, embedder, llm)
  response = agent.chat("Tell me about Paris.")
  ```

## PluginAgent
- **Purpose:** Integrates external tools/plugins, stores results as memories.
- **Key Methods:**
  - `register_plugin(name, func)`
  - `call_plugin(name, *args, **kwargs)`
- **Usage:**
  ```python
  agent = PluginAgent("Plugin", store, embedder)
  agent.register_plugin("add", lambda x, y: x + y)
  result = agent.call_plugin("add", 3, 4)
  ```

## PersonalizationAgent
- **Purpose:** User-specific memory storage and retrieval.
- **Key Methods:**
  - `add_user_memory(text, user_id, uid=None)`
  - `search_for_user(query_text, user_id, top_k=5)`
- **Usage:**
  ```python
  agent = PersonalizationAgent("Personal", store, embedder)
  agent.add_user_memory("User1's secret", user_id="user1")
  results = agent.search_for_user("secret", user_id="user1")
  ```

## ProvenanceAgent
- **Purpose:** Tracks memory source/provenance.
- **Key Methods:**
  - `add_memory(text, source, uid=None)`
  - `search_with_provenance(query_text, source=None, top_k=5)`
- **Usage:**
  ```python
  agent = ProvenanceAgent("Prov", store, embedder)
  agent.add_memory("From Wikipedia", source="wikipedia")
  results = agent.search_with_provenance("from", source="wikipedia")
  ```

## ExpiryAgent
- **Purpose:** Memory expiry and prioritization.
- **Key Methods:**
  - `add_memory(text, priority=1, expiry_seconds=None, uid=None)`
  - `search(query_text, top_k=5)`
- **Usage:**
  ```python
  agent = ExpiryAgent("Expiry", store, embedder)
  agent.add_memory("Short-lived", priority=2, expiry_seconds=1)
  results = agent.search("fact")
  ```

## HybridScoringAgent
- **Purpose:** Hybrid search with weighted scoring (vector, keyword, recency, LLM).
- **Key Methods:**
  - `hybrid_search(query_text, keyword=None, top_k=5, weights=None)`
- **Usage:**
  ```python
  agent = HybridScoringAgent("Hybrid", store, embedder, llm)
  results = agent.hybrid_search("fact", keyword="long", top_k=2)
  ```

## ContextWindowAgent
- **Purpose:** Retrieves and concatenates multiple memories for LLM input (context windowing).
- **Key Methods:**
  - `retrieve_context(query_text, top_k=5)`
  - `answer(user_query)`
- **Usage:**
  ```python
  agent = ContextWindowAgent("Context", store, embedder, llm, max_context=200)
  answer = agent.answer("fact")
  ```

## MultiModalEmbeddingPipeline
- **Purpose:** Embeds both text and images (CLIP-based).
- **Key Methods:**
  - `embed_text(text)`
  - `embed_image(image)`
- **Usage:**
  ```python
  multimodal = MultiModalEmbeddingPipeline()
  text_vec = multimodal.embed_text("A red square")
  # For images: from PIL import Image; img = Image.open(...)
  img_vec = multimodal.embed_image(img)
  ```

## AsyncLLMAgent
- **Purpose:** Async embedding and search for high-throughput scenarios.
- **Key Methods:**
  - `aembed(text)`
  - `aadd_text_memory(text, ...)`
  - `asearch_text(query_text, ...)`
  - `ahybrid_search(query_text, ...)`
- **Usage:**
  ```python
  import asyncio
  agent = AsyncLLMAgent("AsyncDemo", store, embedder)
  await agent.aadd_text_memory("Async: The Eiffel Tower is in Paris.")
  results = await agent.asearch_text("museum")
  ```

---

## Extending Agents
- Subclass any agent and override methods for custom logic.
- Add new metadata fields for richer filtering and retrieval.
- Combine agent types for multi-modal, multi-user, or multi-task scenarios.