import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, dim=384):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(dim)
        self.vectors = []
        self.texts = []

    def add_texts(self, texts):
        embeddings = self.model.encode(texts)
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.vectors.extend(embeddings)
        self.texts.extend(texts)

    def search(self, query, k=5):
        embedding = self.model.encode([query])
        D, I = self.index.search(np.array(embedding, dtype=np.float32), k)
        return [(self.texts[i], float(D[0][idx])) for idx, i in enumerate(I[0])]

    def save(self, path):
        faiss.write_index(self.index, path + ".index")
        np.save(path + ".texts.npy", np.array(self.texts))

    def load(self, path):
        self.index = faiss.read_index(path + ".index")
        self.texts = np.load(path + ".texts.npy").tolist()