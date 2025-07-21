import logging
import time
from typing import Any, List, Optional, Dict, Callable
from faiss_vector_store import FAISSVectorStore

# --- Dependency Checks ---
try:
    from transformers import AutoTokenizer, AutoModel, pipeline, CLIPProcessor, CLIPModel
    import torch
    from PIL import Image
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SuperAdvancedAgents")

# --- Embedding Pipelines ---
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

class MultiModalEmbeddingPipeline:
    def __init__(self, model_name="openai/clip-vit-base-patch16"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers and torch are required for multi-modal embedding.")
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model = CLIPModel.from_pretrained(model_name)
        self.model.eval()

    def embed_text(self, text: str):
        inputs = self.processor(text=[text], images=None, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model.get_text_features(**{k: v for k, v in inputs.items() if k != 'pixel_values'})
        return outputs[0].cpu().numpy()

    def embed_image(self, image: Image.Image):
        inputs = self.processor(text=None, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model.get_image_features(**{k: v for k, v in inputs.items() if k != 'input_ids'})
        return outputs[0].cpu().numpy()

# --- LLM Generator ---
class LLMGenerator:
    def __init__(self, model_name="gpt2"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers is required for LLM generation.")
        self.generator = pipeline("text-generation", model=model_name)

    def generate(self, prompt, max_length=100):
        return self.generator(prompt, max_length=max_length)[0]['generated_text']

# --- Plugin/Tool Agent ---
class PluginAgent:
    def __init__(self, name, vector_store, embedding_pipeline):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.plugins: Dict[str, Callable] = {}

    def register_plugin(self, name: str, func: Callable):
        self.plugins[name] = func

    def call_plugin(self, name: str, *args, **kwargs):
        if name not in self.plugins:
            raise ValueError(f"Plugin {name} not registered.")
        result = self.plugins[name](*args, **kwargs)
        # Store plugin result as memory
        meta = {"text": str(result), "type": "plugin_result", "plugin": name, "timestamp": time.time()}
        self.vector_store.add(self.embedding_pipeline.embed(str(result)), meta)
        return result

# --- Context Windowing/Chunking Agent ---
class ContextWindowAgent:
    def __init__(self, name, vector_store, embedding_pipeline, llm_generator, max_context=1024):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator
        self.max_context = max_context

    def retrieve_context(self, query_text, top_k=5):
        query_vector = self.embedding_pipeline.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k, return_scores=False)
        texts = [meta['text'] for meta in results if meta]
        context = ''
        for t in texts:
            if len(context) + len(t) > self.max_context:
                break
            context += t + '\n'
        return context.strip()

    def answer(self, user_query):
        context = self.retrieve_context(user_query)
        prompt = f"Context:\n{context}\n\nUser: {user_query}\nAgent:"
        return self.llm_generator.generate(prompt, max_length=150)

# --- Memory Expiry/Prioritization Agent ---
class ExpiryAgent:
    def __init__(self, name, vector_store, embedding_pipeline):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline

    def add_memory(self, text, priority=1, expiry_seconds=None, uid=None):
        meta = {"text": text, "priority": priority, "timestamp": time.time()}
        if expiry_seconds:
            meta["expiry"] = time.time() + expiry_seconds
        self.vector_store.add(self.embedding_pipeline.embed(text), meta, uid)

    def search(self, query_text, top_k=5):
        now = time.time()
        query_vector = self.embedding_pipeline.embed(query_text)
        def filter_fn(meta):
            if not meta:
                return False
            if meta.get("expiry") and meta["expiry"] < now:
                return False
            return True
        results = self.vector_store.search_with_filter(query_vector, top_k, filter_fn, return_scores=True)
        # Sort by priority, then recency
        results.sort(key=lambda x: (-x[0].get("priority", 1), -x[0].get("timestamp", 0)))
        return results

# --- User Personalization Agent ---
class PersonalizationAgent:
    def __init__(self, name, vector_store, embedding_pipeline, encryption_agent=None):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.encryption_agent = encryption_agent

    def add_user_memory(self, text, user_id, uid=None):
        if self.encryption_agent:
            text = self.encryption_agent.encrypt(text)
        meta = {"text": text, "user_id": user_id, "timestamp": time.time()}
        self.vector_store.add(self.embedding_pipeline.embed(text), meta, uid)

    def search_for_user(self, query_text, user_id, top_k=5):
        query_vector = self.embedding_pipeline.embed(query_text)
        def filter_fn(meta):
            return meta and meta.get("user_id") == user_id

        results = self.vector_store.search_with_filter(query_vector, top_k, filter_fn, return_scores=True)

        if self.encryption_agent:
            decrypted_results = []
            for meta, score, uid in results:
                if meta and "text" in meta:
                    meta["text"] = self.encryption_agent.decrypt(meta["text"])
                decrypted_results.append((meta, score, uid))
            return decrypted_results
        return results

# --- Provenance Agent ---
class ProvenanceAgent:
    def __init__(self, name, vector_store, embedding_pipeline):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline

    def add_memory(self, text, source, uid=None):
        meta = {"text": text, "source": source, "timestamp": time.time()}
        self.vector_store.add(self.embedding_pipeline.embed(text), meta, uid)

    def search_with_provenance(self, query_text, source=None, top_k=5):
        query_vector = self.embedding_pipeline.embed(query_text)
        def filter_fn(meta):
            return meta and (source is None or meta.get("source") == source)
        return self.vector_store.search_with_filter(query_vector, top_k, filter_fn, return_scores=True)

# --- Hybrid Weighted Scoring Agent ---
class HybridScoringAgent:
    def __init__(self, name, vector_store, embedding_pipeline, llm_generator=None):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator

    def hybrid_search(self, query_text, keyword=None, top_k=5, weights=None):
        if weights is None:
            weights = {"vector": 0.5, "keyword": 0.2, "recency": 0.2, "llm": 0.1}
        query_vector = self.embedding_pipeline.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k*3, return_scores=True)
        now = time.time()
        scored = []
        for meta, vec_score, uid in results:
            if not meta:
                continue
            keyword_score = 1.0 if keyword and keyword.lower() in meta.get("text", "").lower() else 0.0
            recency_score = 1.0 / (1.0 + (now - meta.get("timestamp", now)))
            llm_score = 0.0
            if self.llm_generator:
                prompt = f"How relevant is the following memory to the query '{query_text}'? Memory: {meta['text']}\nScore 1-10:"
                llm_out = self.llm_generator.generate(prompt, max_length=20)
                try:
                    llm_score = float(''.join(filter(str.isdigit, llm_out))) / 10.0
                except Exception:
                    llm_score = 0.0
            final_score = (weights["vector"] * (1.0 / (1.0 + vec_score)) +
                           weights["keyword"] * keyword_score +
                           weights["recency"] * recency_score +
                           weights["llm"] * llm_score)
            scored.append((meta, final_score, uid))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

# --- Distributed Vector Store Stub (for demo) ---
class DistributedVectorStoreStub:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        # In a real system, this would be a REST/gRPC client
    def add(self, *args, **kwargs):
        return self.vector_store.add(*args, **kwargs)
    def search(self, *args, **kwargs):
        return self.vector_store.search(*args, **kwargs)

# --- Async LLM Calls Example ---
import asyncio
from concurrent.futures import ThreadPoolExecutor
class AsyncLLMWrapper:
    def __init__(self, llm_generator):
        self.llm_generator = llm_generator
        self._executor = ThreadPoolExecutor()
    async def agenerate(self, prompt, max_length=100):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.llm_generator.generate, prompt, max_length)

# --- Demo Block ---
if __name__ == "__main__":
    if not HF_AVAILABLE:
        print("HuggingFace Transformers, torch, and PIL are required for this demo.")
    else:
        # Shared store and pipelines
        store = FAISSVectorStore(dim=384)
        embedder = EmbeddingPipeline()
        multimodal = MultiModalEmbeddingPipeline()
        llm = LLMGenerator()
        async_llm = AsyncLLMWrapper(llm)

        # --- Memory Expiry/Prioritization ---
        expiry_agent = ExpiryAgent("Expiry", store, embedder)
        expiry_agent.add_memory("Short-lived fact", priority=2, expiry_seconds=1, uid="short")
        expiry_agent.add_memory("Long-lived fact", priority=1, expiry_seconds=1000, uid="long")
        time.sleep(2)
        print("\n--- ExpiryAgent Search (should only show long-lived) ---")
        print(expiry_agent.search("fact"))

        # --- Plugin/Tool Use ---
        plugin_agent = PluginAgent("Plugin", store, embedder)
        plugin_agent.register_plugin("add", lambda x, y: x + y)
        print("\n--- PluginAgent Plugin Call ---")
        print(plugin_agent.call_plugin("add", 3, 4))

        # --- Multi-modal Memory ---
        try:
            img = Image.new('RGB', (64, 64), color = 'red')
            img_vec = multimodal.embed_image(img)
            store.add(img_vec, {"text": "A red square image", "type": "image"}, uid="img1")
            print("\n--- MultiModalEmbeddingPipeline Image Embedding Added ---")
        except Exception as e:
            print("Multi-modal embedding demo skipped (PIL or CLIP not available):", e)

        # --- Context Windowing/Chunking ---
        context_agent = ContextWindowAgent("Context", store, embedder, llm, max_context=200)
        print("\n--- ContextWindowAgent Answer ---")
        print(context_agent.answer("fact"))

        # --- User Personalization ---
        pers_agent = PersonalizationAgent("Personal", store, embedder)
        pers_agent.add_user_memory("User1's secret", user_id="user1")
        pers_agent.add_user_memory("User2's secret", user_id="user2")
        print("\n--- PersonalizationAgent Search for user1 ---")
        print(pers_agent.search_for_user("secret", user_id="user1"))

        # --- Provenance ---
        prov_agent = ProvenanceAgent("Prov", store, embedder)
        prov_agent.add_memory("From Wikipedia", source="wikipedia")
        prov_agent.add_memory("From user", source="user")
        print("\n--- ProvenanceAgent Search for source 'wikipedia' ---")
        print(prov_agent.search_with_provenance("from", source="wikipedia"))

        # --- Hybrid Weighted Scoring ---
        hybrid_agent = HybridScoringAgent("Hybrid", store, embedder, llm)
        print("\n--- HybridScoringAgent Hybrid Search ---")
        print(hybrid_agent.hybrid_search("fact", keyword="long", top_k=2))

        # --- Distributed Vector Store Stub ---
        dist_store = DistributedVectorStoreStub(store)
        print("\n--- DistributedVectorStoreStub Search ---")
        print(dist_store.search([0.0]*384, top_k=1))

        # --- Async LLM Call ---
        async def async_demo():
            print("\n--- AsyncLLMWrapper agenerate ---")
            result = await async_llm.agenerate("Say hello to the world!", max_length=20)
            print(result)
        asyncio.run(async_demo())