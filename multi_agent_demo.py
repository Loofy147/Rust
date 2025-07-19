from advanced_agent import AdvancedAgent
from faiss_vector_store import FAISSVectorStore
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Shared vector store (4D for demo)
    shared_store = FAISSVectorStore(dim=4, index_type='flat')

    # Create two agents sharing the same store
    agent_alice = AdvancedAgent("Alice", shared_store)
    agent_bob = AdvancedAgent("Bob", shared_store)

    # Alice adds her memories
    agent_alice.add_memory([1,0,0,0], "Alice: Paris is beautiful in spring", memory_type="travel", uid="alice1")
    agent_alice.add_memory([0,1,0,0], "Alice: I love croissants", memory_type="food", uid="alice2")

    # Bob adds his memories
    agent_bob.add_memory([0,0,1,0], "Bob: Berlin has great museums", memory_type="travel", uid="bob1")
    agent_bob.add_memory([0,0,0,1], "Bob: Currywurst is tasty", memory_type="food", uid="bob2")

    print("\n--- Alice searches for travel memories ---")
    results = agent_alice.search_memory([1,0,0,0], top_k=3, memory_type="travel")
    for meta in results:
        print(meta)

    print("\n--- Bob searches for food memories ---")
    results = agent_bob.search_memory([0,0,0,1], top_k=3, memory_type="food")
    for meta in results:
        print(meta)

    print("\n--- Alice searches for all memories (no filter) ---")
    results = agent_alice.search_memory([1,0,0,0], top_k=4)
    for meta in results:
        print(meta)

    print("\n--- Bob searches for Alice's travel memories only ---")
    results = agent_bob.search_memory([1,0,0,0], top_k=4, filter_fn=lambda m: m and m.get("agent") == "Alice" and m.get("type") == "travel")
    for meta in results:
        print(meta)

    print("\n--- Stats for shared store ---")
    print(shared_store.index_type, "count:", len(shared_store.metadata))