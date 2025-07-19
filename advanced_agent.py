import logging
from typing import Any, Callable, List, Optional
from faiss_vector_store import FAISSVectorStore

logger = logging.getLogger("AdvancedAgent")
logging.basicConfig(level=logging.INFO)

class AdvancedAgent:
    def __init__(self, name: str, vector_store: FAISSVectorStore):
        self.name = name
        self.vector_store = vector_store
        logger.info(f"Agent '{self.name}' initialized with vector store.")

    def add_memory(self, vector: List[float], text: str, memory_type: str = "fact", uid: Optional[str] = None, extra: Optional[dict] = None):
        metadata = {"text": text, "agent": self.name, "type": memory_type}
        if extra:
            metadata.update(extra)
        self.vector_store.add(vector, metadata, uid)
        logger.info(f"Added memory: {metadata} (uid={uid})")

    def add_memories_batch(self, vectors: List[List[float]], texts: List[str], memory_type: str = "fact", uids: Optional[List[str]] = None, extras: Optional[List[dict]] = None):
        metadatas = []
        for i, text in enumerate(texts):
            meta = {"text": text, "agent": self.name, "type": memory_type}
            if extras and extras[i]:
                meta.update(extras[i])
            metadatas.append(meta)
        self.vector_store.add_batch(vectors, metadatas, uids)
        logger.info(f"Batch added {len(vectors)} memories.")

    def search_memory(self, query_vector: List[float], top_k: int = 5, memory_type: Optional[str] = None, filter_fn: Optional[Callable[[Any], bool]] = None, return_scores: bool = True):
        def combined_filter(meta):
            if memory_type and (not meta or meta.get("type") != memory_type):
                return False
            if filter_fn and not filter_fn(meta):
                return False
            return True
        results = self.vector_store.search_with_filter(query_vector, top_k, combined_filter, return_scores=return_scores)
        logger.info(f"Search returned {len(results)} results.")
        return results

    def get_memory_by_id(self, uid: str):
        memory = self.vector_store.get_by_id(uid)
        logger.info(f"Get by id {uid}: {memory}")
        return memory

    def update_memory(self, uid: str, new_vector: List[float], new_text: Optional[str] = None, new_type: Optional[str] = None, new_extra: Optional[dict] = None):
        old_meta = self.vector_store.get_by_id(uid) or {}
        new_meta = old_meta.copy()
        if new_text:
            new_meta["text"] = new_text
        if new_type:
            new_meta["type"] = new_type
        if new_extra:
            new_meta.update(new_extra)
        self.vector_store.update(uid, new_vector, new_meta)
        logger.info(f"Updated memory {uid}: {new_meta}")

    def delete_memory(self, uid: str):
        self.vector_store.mark_deleted(uid)
        logger.info(f"Deleted memory {uid}")

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
    import numpy as np
    # Create a FAISS vector store (4D for demo)
    store = FAISSVectorStore(dim=4, index_type='flat')
    agent = AdvancedAgent("DemoAgent", store)
    # Add memories
    agent.add_memory([1,0,0,0], "Paris is the capital of France", memory_type="fact", uid="fact1")
    agent.add_memory([0,1,0,0], "Berlin is the capital of Germany", memory_type="fact", uid="fact2")
    # Batch add
    agent.add_memories_batch(
        vectors=[[0,0,1,0],[0,0,0,1]],
        texts=["Rome is the capital of Italy", "Madrid is the capital of Spain"],
        memory_type="fact",
        uids=["fact3","fact4"]
    )
    # Search
    print("Search results:", agent.search_memory([1,0,0,0], top_k=2))
    # Filtered search
    print("Filtered search:", agent.search_memory([1,0,0,0], top_k=2, memory_type="fact"))
    # Get by ID
    print("Get by id fact3:", agent.get_memory_by_id("fact3"))
    # Update
    agent.update_memory("fact1", [0.5,0.5,0,0], new_text="Paris is in France", new_type="updated_fact")
    print("After update:", agent.get_memory_by_id("fact1"))
    # Delete
    agent.delete_memory("fact2")
    print("After delete:", agent.get_memory_by_id("fact2"))
    # Save/load
    agent.save_agent_memory()
    agent2 = AdvancedAgent("DemoAgent", FAISSVectorStore(dim=4))
    agent2.load_agent_memory()
    print("Loaded agent2 search:", agent2.search_memory([0,0,1,0], top_k=2))
    # Stats
    print("Memory stats:", agent.get_memory_stats())