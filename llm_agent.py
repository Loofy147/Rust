import logging
from typing import Any, Callable, List, Optional
from faiss_vector_store import FAISSVectorStore

# --- Embedding Pipeline ---
try:
    from transformers import AutoTokenizer, AutoModel, pipeline
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logger = logging.getLogger("LLMAgent")
logging.basicConfig(level=logging.INFO)

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

# --- LLM Generator ---
class LLMGenerator:
    def __init__(self, model_name="gpt2"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers is required for LLM generation.")
        self.generator = pipeline("text-generation", model=model_name)

    def generate(self, prompt, max_length=100):
        return self.generator(prompt, max_length=max_length)[0]['generated_text']

# --- LLM-Integrated Agent ---
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

    def add_memories_batch(self, texts: List[str], memory_type: str = "fact", uids: Optional[List[str]] = None, extras: Optional[List[dict]] = None):
        vectors = [self.embedding_pipeline.embed(text) for text in texts]
        metadatas = []
        for i, text in enumerate(texts):
            meta = {"text": text, "agent": self.name, "type": memory_type}
            if extras and extras[i]:
                meta.update(extras[i])
            metadatas.append(meta)
        self.vector_store.add_batch(vectors, metadatas, uids)
        logger.info(f"Batch added {len(vectors)} memories.")

    def search_text(self, query_text: str, top_k: int = 5, memory_type: Optional[str] = None, filter_fn: Optional[Callable[[Any], bool]] = None, return_scores: bool = True):
        query_vector = self.embedding_pipeline.embed(query_text)
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

    def generate_on_memory(self, prompt_prefix: str, memory_result):
        if not self.llm_generator:
            raise RuntimeError("No LLM generator provided.")
        meta = memory_result[0] if isinstance(memory_result, tuple) else memory_result
        prompt = f"{prompt_prefix} {meta['text']}"
        return self.llm_generator.generate(prompt)

    def get_memory_by_id(self, uid: str):
        memory = self.vector_store.get_by_id(uid)
        logger.info(f"Get by id {uid}: {memory}")
        return memory

    def save_agent_memory(self):
        self.vector_store.save(f"{self.name}_index.faiss", f"{self.name}_meta.pkl")
        logger.info(f"Agent memory saved.")

    def load_agent_memory(self):
        self.vector_store.load(f"{self.name}_index.faiss", f"{self.name}_meta.pkl")
        logger.info(f"Agent memory loaded.")

    def get_memory_stats(self):
        stats = {
            "count": len(self.vector_store.metadata),
            "index_type": self.vector_store.index_type,
            "is_trained": getattr(self.vector_store.index, 'is_trained', True)
        }
        logger.info(f"Memory stats: {stats}")
        return stats

# --- Example Usage ---
if __name__ == "__main__":
    if not HF_AVAILABLE:
        print("HuggingFace Transformers and torch are required for this demo.")
    else:
        # Setup
        store = FAISSVectorStore(dim=384)
        embedder = EmbeddingPipeline()
        llm = LLMGenerator()
        agent = LLMAgent("LLMAgentDemo", store, embedder, llm)

        # Add text memories
        agent.add_text_memory("The Eiffel Tower is in Paris.", memory_type="fact", uid="eiffel")
        agent.add_text_memory("The Louvre is a famous museum.", memory_type="fact", uid="louvre")
        agent.add_text_memory("Berlin has the Brandenburg Gate.", memory_type="fact", uid="berlin")
        agent.add_text_memory("The Colosseum is in Rome.", memory_type="fact", uid="colosseum")

        # Hybrid search: semantic + keyword
        print("\nHybrid search for 'museum' with keyword 'Louvre':")
        results = agent.hybrid_search("museum", keyword="Louvre", top_k=2)
        for meta, score, uid in results:
            print(f"UID: {uid}, Score: {score:.4f}, Text: {meta['text']}")

        # LLM generation on retrieved memory
        if results:
            prompt = "Summarize:"
            print("\nLLM summary:", agent.generate_on_memory(prompt, results[0]))

        # Save/load
        agent.save_agent_memory()
        agent2 = LLMAgent("LLMAgentDemo", FAISSVectorStore(dim=384), embedder, llm)
        agent2.load_agent_memory()
        print("\nLoaded agent2 hybrid search for 'Rome':")
        results2 = agent2.hybrid_search("Rome", keyword="Colosseum", top_k=2)
        for meta, score, uid in results2:
            print(f"UID: {uid}, Score: {score:.4f}, Text: {meta['text']}")
        print("\nMemory stats:", agent2.get_memory_stats())