# Vector Store Documentation

This document describes the vector store components in the Super Advanced Agent Framework.

## FAISSVectorStore

A high-performance, extensible vector store built on [FAISS](https://github.com/facebookresearch/faiss).

### Initialization
```python
from faiss_vector_store import FAISSVectorStore
store = FAISSVectorStore(dim=384, index_type='flat')
```
- `dim`: Dimensionality of your embeddings (e.g., 384 for MiniLM, 512/768 for BERT, etc.)
- `index_type`: 'flat', 'ivf', or 'hnsw' (see FAISS docs for details)

### Adding Vectors
```python
vector = [0.1, 0.2, ...]  # Your embedding
metadata = {"text": "Paris is the capital of France"}
store.add(vector, metadata, uid="fact1")
```
- `metadata` can be any dict (text, type, user, timestamp, etc.)
- `uid` is an optional unique identifier

### Batch Operations
```python
vectors = [[...], [...], ...]
metadatas = [{...}, {...}, ...]
uids = ["id1", "id2", ...]
store.add_batch(vectors, metadatas, uids)
```

### Searching
```python
results = store.search(query_vector, top_k=5, return_scores=True)
# Returns list of (metadata, score, uid)
```

### Metadata Filtering
```python
def filter_fn(meta):
    return meta and meta.get("type") == "fact"
results = store.search_with_filter(query_vector, top_k=5, filter_fn=filter_fn)
```

### Persistence
```python
store.save('faiss.index', 'meta.pkl')
store.load('faiss.index', 'meta.pkl')
```

### Hybrid Search
Combine vector similarity with keyword, recency, or LLM-based scoring using HybridScoringAgent.

### Multi-modal Support
Use with MultiModalEmbeddingPipeline for text and image embeddings.

## MultiModalEmbeddingPipeline

Embeds both text and images using CLIP.

```python
from super_advanced_agents import MultiModalEmbeddingPipeline
from PIL import Image
multimodal = MultiModalEmbeddingPipeline()
text_vec = multimodal.embed_text("A red square")
img = Image.open("red_square.png")
img_vec = multimodal.embed_image(img)
```

## Best Practices
- Use batch operations for efficiency.
- Regularly save/load the index for persistence.
- Use rich metadata for filtering and advanced retrieval.
- For large-scale or distributed use, consider sharding or REST/gRPC wrappers.

## Extension Points
- Add new index types or backends (e.g., Pinecone, Milvus) by subclassing the base VectorStore.
- Implement custom filtering, scoring, or hybrid search logic as needed.