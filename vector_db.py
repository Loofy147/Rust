import faiss
import numpy as np

class SimpleFaissDB:
    def __init__(self, dim=384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.data = []  # List of (id, vector, payload)

    def upsert(self, vec_id, vector, payload=None):
        vector = np.array(vector).astype('float32').reshape(1, -1)
        self.index.add(vector)
        self.data.append((vec_id, vector.tolist(), payload))

    def search(self, vector, k=5):
        vector = np.array(vector).astype('float32').reshape(1, -1)
        D, I = self.index.search(vector, k)
        results = []
        for idx in I[0]:
            if idx < len(self.data):
                results.append(self.data[idx])
        return results