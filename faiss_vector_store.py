import faiss
import numpy as np
import pickle
from abc import ABC, abstractmethod

class VectorStore(ABC):
    @abstractmethod
    def add(self, vector, metadata=None):
        pass

    @abstractmethod
    def search(self, query_vector, top_k=5):
        pass

    @abstractmethod
    def save(self, index_path, meta_path):
        pass

    @abstractmethod
    def load(self, index_path, meta_path):
        pass

class FAISSVectorStore(VectorStore):
    def __init__(self, dim):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

    def add(self, vector, metadata=None):
        vector = np.array(vector).astype('float32').reshape(1, -1)
        self.index.add(vector)
        self.metadata.append(metadata)

    def search(self, query_vector, top_k=5):
        query_vector = np.array(query_vector).astype('float32').reshape(1, -1)
        D, I = self.index.search(query_vector, top_k)
        results = []
        for idx in I[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results

    def save(self, index_path, meta_path):
        faiss.write_index(self.index, index_path)
        with open(meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def load(self, index_path, meta_path):
        self.index = faiss.read_index(index_path)
        with open(meta_path, 'rb') as f:
            self.metadata = pickle.load(f)

def test_faiss_store():
    print("Testing FAISSVectorStore...")
    store = FAISSVectorStore(dim=3)
    store.add([1, 0, 0], metadata="A")
    store.add([0, 1, 0], metadata="B")
    store.add([0, 0, 1], metadata="C")
    results = store.search([1, 0, 0], top_k=2)
    print("Search results for [1, 0, 0] (top 2):", results)
    # Test save/load
    store.save('faiss.index', 'meta.pkl')
    new_store = FAISSVectorStore(dim=3)
    new_store.load('faiss.index', 'meta.pkl')
    new_results = new_store.search([0, 1, 0], top_k=2)
    print("Search results after reload for [0, 1, 0] (top 2):", new_results)

if __name__ == "__main__":
    test_faiss_store()