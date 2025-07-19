import chromadb
from agent.interfaces import VectorStorePlugin

class ChromaVectorStore(VectorStorePlugin):
    def __init__(self, collection_name="my_vectors"):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(collection_name)

    def add(self, vector, metadata):
        self.collection.add(
            embeddings=[vector],
            metadatas=[metadata],
            ids=[metadata.get("id")]
        )

    def query(self, vector, top_k: int):
        return self.collection.query(query_embeddings=[vector], n_results=top_k)