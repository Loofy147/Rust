import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os

class ChromaVectorStore:
    def __init__(self, persist_dir="./chroma_data"):
        self.client = chromadb.Client(Settings(persist_directory=persist_dir))
        self.collection = self.client.get_or_create_collection("llm_vectors")
        self.embedder = SentenceTransformer(os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2"))

    def upsert(self, id: str, text: str, metadata: dict = None):
        embedding = self.embedder.encode([text])[0].tolist()
        self.collection.upsert(
            ids=[id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )

    def query(self, text: str, top_k: int = 5):
        embedding = self.embedder.encode([text])[0].tolist()
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        return results