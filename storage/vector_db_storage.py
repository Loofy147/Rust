import faiss
import numpy as np

class VectorDBStorageBackend:
    def __init__(self, config):
        self.dim = config.get('dim', 384)
        self.index = faiss.IndexFlatL2(self.dim)
        self.data = []
    def save(self, item):
        vector = np.array(item['vector']).astype('float32').reshape(1, -1)
        self.index.add(vector)
        self.data.append(item)
    def load(self):
        return self.data
    def search(self, vector, k=5):
        vector = np.array(vector).astype('float32').reshape(1, -1)
        D, I = self.index.search(vector, k)
        return [self.data[i] for i in I[0] if i < len(self.data)]