import os
from agent.plugins.kg_sqlalchemy import SQLAlchemyKG
from agent.plugins.vector_chroma import ChromaVectorStore

def seed_kg(kg):
    kg.store({"id": "sample1", "type": "note", "data": "This is a sample KG node."})
    kg.store({"id": "sample2", "type": "note", "data": "Another sample node."})

def seed_vectors(vector_store):
    vector_store.add([0.1, 0.2, 0.3], {"id": "sample1"})
    vector_store.add([0.4, 0.5, 0.6], {"id": "sample2"})

def main():
    kg = SQLAlchemyKG(os.getenv("DB_URL", "sqlite:///kg.db"))
    vector_store = ChromaVectorStore()
    seed_kg(kg)
    seed_vectors(vector_store)
    print("Sample data seeded.")

if __name__ == "__main__":
    main()