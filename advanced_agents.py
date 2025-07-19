import logging
from faiss_vector_store import FAISSVectorStore
from typing import Any, List, Optional

# Embedding and LLM generator
try:
    from transformers import AutoTokenizer, AutoModel, pipeline
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdvancedAgents")

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

class LLMGenerator:
    def __init__(self, model_name="gpt2"):
        if not HF_AVAILABLE:
            raise ImportError("HuggingFace Transformers is required for LLM generation.")
        self.generator = pipeline("text-generation", model=model_name)

    def generate(self, prompt, max_length=100):
        return self.generator(prompt, max_length=max_length)[0]['generated_text']

# --- RetrieverAgent ---
class RetrieverAgent:
    def __init__(self, name, vector_store, embedding_pipeline, llm_generator=None):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator

    def retrieve(self, query_text, top_k=5, keyword=None, memory_type=None):
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
        return filtered

    def rerank_with_llm(self, query_text, results):
        if not self.llm_generator:
            return results
        reranked = []
        for meta, score, uid in results:
            prompt = f"How relevant is the following memory to the query '{query_text}'? Memory: {meta['text']}\nScore 1-10:"
            llm_score = self.llm_generator.generate(prompt, max_length=20)
            try:
                llm_score = float(''.join(filter(str.isdigit, llm_score)))
            except Exception:
                llm_score = 0
            reranked.append((meta, score, uid, llm_score))
        reranked.sort(key=lambda x: -x[3])
        return reranked

# --- SummarizerAgent ---
class SummarizerAgent:
    def __init__(self, name, vector_store, embedding_pipeline, llm_generator):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator

    def summarize_memories(self, query_text, top_k=5, memory_type=None):
        query_vector = self.embedding_pipeline.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k, return_scores=False)
        texts = [meta['text'] for meta in results if meta]
        if not texts:
            return "No relevant memories found."
        prompt = "Summarize the following information:\n" + "\n".join(texts)
        return self.llm_generator.generate(prompt, max_length=150)

# --- ConversationalAgent ---
class ConversationalAgent:
    def __init__(self, name, vector_store, embedding_pipeline, llm_generator):
        self.name = name
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.llm_generator = llm_generator

    def add_turn(self, user_text, agent_text, turn_id=None):
        self.vector_store.add(self.embedding_pipeline.embed(user_text), {"text": user_text, "role": "user", "agent": self.name}, f"{turn_id}_user" if turn_id else None)
        self.vector_store.add(self.embedding_pipeline.embed(agent_text), {"text": agent_text, "role": "agent", "agent": self.name}, f"{turn_id}_agent" if turn_id else None)

    def get_context(self, query_text, top_k=3):
        query_vector = self.embedding_pipeline.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k, return_scores=False)
        return [meta['text'] for meta in results if meta]

    def chat(self, user_text):
        context = self.get_context(user_text, top_k=3)
        prompt = "You are a helpful assistant. Here is the conversation so far:\n" + "\n".join(context) + f"\nUser: {user_text}\nAgent:"
        response = self.llm_generator.generate(prompt, max_length=100)
        self.add_turn(user_text, response)
        return response

# --- Demo Block ---
if __name__ == "__main__":
    if not HF_AVAILABLE:
        print("HuggingFace Transformers and torch are required for this demo.")
    else:
        # Shared store and pipelines
        store = FAISSVectorStore(dim=384)
        embedder = EmbeddingPipeline()
        llm = LLMGenerator()

        # Populate store with some facts
        facts = [
            ("The Eiffel Tower is in Paris.", "fact", "eiffel"),
            ("The Louvre is a famous museum.", "fact", "louvre"),
            ("Berlin has the Brandenburg Gate.", "fact", "berlin"),
            ("The Colosseum is in Rome.", "fact", "colosseum"),
            ("Paris is known for its cafes.", "fact", "paris_cafe"),
        ]
        for text, typ, uid in facts:
            store.add(embedder.embed(text), {"text": text, "type": typ}, uid)

        print("\n--- RetrieverAgent Demo ---")
        retriever = RetrieverAgent("Retriever", store, embedder, llm)
        results = retriever.retrieve("museum", top_k=3, keyword="Louvre")
        for meta, score, uid in results:
            print(f"UID: {uid}, Score: {score:.4f}, Text: {meta['text']}")
        reranked = retriever.rerank_with_llm("museum", results)
        print("\nLLM Reranked Results:")
        for meta, score, uid, llm_score in reranked:
            print(f"UID: {uid}, LLM Score: {llm_score}, Text: {meta['text']}")

        print("\n--- SummarizerAgent Demo ---")
        summarizer = SummarizerAgent("Summarizer", store, embedder, llm)
        summary = summarizer.summarize_memories("Paris", top_k=3)
        print("Summary for Paris:", summary)

        print("\n--- ConversationalAgent Demo ---")
        conv = ConversationalAgent("Chatty", store, embedder, llm)
        # Simulate a conversation
        user_turns = [
            "Hi, what do you know about Paris?",
            "Tell me about famous landmarks.",
            "What about Rome?"
        ]
        for i, user_text in enumerate(user_turns):
            response = conv.chat(user_text)
            print(f"User: {user_text}\nAgent: {response}\n")