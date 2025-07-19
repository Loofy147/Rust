import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional
from faiss_vector_store import FAISSVectorStore

# Import embedding and LLM generator from llm_agent.py
try:
    from transformers import AutoTokenizer, AutoModel, pipeline
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AsyncLLMAgent")

# --- Embedding Pipeline (same as llm_agent.py) ---
class EmbeddingPipeline:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers and torch are required for embedding.")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def embed(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            model_output = self.model(**inputs)
        embeddings = model_output.last_hidden_state.mean(dim=1)
        return embeddings[0].cpu().numpy()

# --- LLM Generator (same as llm_agent.py) ---
class LLMGenerator:
    def __init__(self, model_name="gpt2"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers is required for LLM generation.")
        self.generator = pipeline("text-generation", model=model_name)

    def generate(self, prompt, max_length=100):
        return self.generator(prompt, max_length=max_length)[0]['generated_text']

# --- LLMAgent (sync base) ---
class LLMAgent:
    def __init__(self, name: str, vector_store: FAISSVectorStore, embedding_pipeline: EmbeddingPipeline, llm_generator: Optional[LLMGenerator] = None):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator
        logger.info(f"LLMAgent '{self.name}' initialized.")

    def add_text_memory(self, text: str, memory_type: str = "fact", uid: Optional[str] = None, extra: Optional[dict] = None):
        vector = self.embedding_pipeline.embed(text)
        metadata = {"text": text, "agent": self.name, "type": memory_type}
        if extra:
            metadata.update(extra)
        self.vector_store.add(vector, metadata, uid)
        logger.info(f"Added memory: {metadata} (uid={uid})")

    def search_memory(self, query_vector, top_k=5, memory_type: Optional[str] = None, filter_fn: Optional[Callable[[Any], bool]] = None, return_scores: bool = True):
        def combined_filter(meta):
            if memory_type and (not meta or meta.get("type") != memory_type):
                return False
            if filter_fn and not filter_fn(meta):
                return False
            return True
        results = self.vector_store.search_with_filter(query_vector, top_k, combined_filter, return_scores=return_scores)
        logger.info(f"Search returned {len(results)} results.")
        return results

    def hybrid_search(self, query_text: str, keyword: Optional[str] = None, top_k: int = 5, memory_type: Optional[str] = None):
        query_vector = self.embedding_pipeline.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k*2, return_scores=True)
        filtered = []
        for meta, score, uid in results:
            if memory_type and (not meta or meta.get("type") != memory_type):
                continue
            if keyword and keyword.lower() not in meta.get('text', '').lower():
                continue
            filtered.append((meta, score, uid))
            if len(filtered) >= top_k:
                break
        logger.info(f"Hybrid search returned {len(filtered)} results.")
        return filtered

# --- AsyncLLMAgent ---
class AsyncLLMAgent(LLMAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._executor = ThreadPoolExecutor()

    async def aembed(self, text):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.embedding_pipeline.embed, text)

    async def aadd_text_memory(self, text, memory_type="fact", uid=None, extra=None):
        vector = await self.aembed(text)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor, self.vector_store.add, vector, {"text": text, "agent": self.name, "type": memory_type} if not extra else {**{"text": text, "agent": self.name, "type": memory_type}, **extra}, uid
        )
        logger.info(f"[Async] Added memory: {text} (uid={uid})")

    async def asearch_text(self, query_text, top_k=5, memory_type=None, filter_fn=None, return_scores=True):
        query_vector = await self.aembed(query_text)
        loop = asyncio.get_event_loop()
        def combined_filter(meta):
            if memory_type and (not meta or meta.get("type") != memory_type):
                return False
            if filter_fn and not filter_fn(meta):
                return False
            return True
        return await loop.run_in_executor(
            self._executor, self.vector_store.search_with_filter, query_vector, top_k, combined_filter, return_scores
        )

    async def ahybrid_search(self, query_text, keyword=None, top_k=5, memory_type=None):
        query_vector = await self.aembed(query_text)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self._executor, self.vector_store.search, query_vector, top_k*2, True
        )
        filtered = []
        for meta, score, uid in results:
            if memory_type and (not meta or meta.get("type") != memory_type):
                continue
            if keyword and keyword.lower() not in meta.get('text', '').lower():
                continue
            filtered.append((meta, score, uid))
            if len(filtered) >= top_k:
                break
        logger.info(f"[Async] Hybrid search returned {len(filtered)} results.")
        return filtered

# --- Demo ---
if __name__ == "__main__":
    if not HF_AVAILABLE:
        print("HuggingFace Transformers and torch are required for this demo.")
    else:
        async def main():
            store = FAISSVectorStore(dim=384)
            embedder = EmbeddingPipeline()
            agent = AsyncLLMAgent("AsyncDemoAgent", store, embedder)

            # Concurrently add memories
            await asyncio.gather(
                agent.aadd_text_memory("Async: The Eiffel Tower is in Paris.", memory_type="fact", uid="eiffel"),
                agent.aadd_text_memory("Async: The Louvre is a famous museum.", memory_type="fact", uid="louvre"),
                agent.aadd_text_memory("Async: Berlin has the Brandenburg Gate.", memory_type="fact", uid="berlin"),
                agent.aadd_text_memory("Async: The Colosseum is in Rome.", memory_type="fact", uid="colosseum")
            )

            # Concurrent searches
            results = await asyncio.gather(
                agent.asearch_text("museum", top_k=2),
                agent.ahybrid_search("museum", keyword="Louvre", top_k=2),
                agent.asearch_text("Rome", top_k=2)
            )
            print("\nAsync search for 'museum':", results[0])
            print("\nAsync hybrid search for 'museum' with keyword 'Louvre':", results[1])
            print("\nAsync search for 'Rome':", results[2])

        asyncio.run(main())