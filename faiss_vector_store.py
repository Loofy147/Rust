import faiss
import numpy as np
import pickle
import threading
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FAISSVectorStore")

class VectorStore(ABC):
    @abstractmethod
    def add(self, vector, metadata=None, uid=None):
        pass

    @abstractmethod
    def add_batch(self, vectors, metadatas=None, uids=None):
        pass

    @abstractmethod
    def search(self, query_vector, top_k=5, return_scores=False):
        pass

    @abstractmethod
    def search_batch(self, query_vectors, top_k=5, return_scores=False):
        pass

    @abstractmethod
    def search_with_filter(self, query_vector, top_k=5, filter_fn=None, return_scores=False):
        pass

    @abstractmethod
    def get_by_id(self, uid):
        pass

    @abstractmethod
    def save(self, index_path, meta_path):
        pass

    @abstractmethod
    def load(self, index_path, meta_path):
        pass

class FAISSVectorStore(VectorStore):
    def __init__(self, dim: int, index_type: str = 'flat', nlist: int = 100, hnsw_m: int = 32):
        self.dim = dim
        self.lock = threading.Lock()
        self.index_type = index_type
        self.nlist = nlist
        self.hnsw_m = hnsw_m
        self._init_index()
        self.metadata: List[Any] = []
        self.id_to_idx: Dict[Any, int] = {}
        self.idx_to_id: Dict[int, Any] = {}
        logger.info(f"Initialized FAISSVectorStore with index_type={index_type}, dim={dim}")

    def _init_index(self):
        if self.index_type == 'flat':
            self.index = faiss.IndexFlatL2(self.dim)
        elif self.index_type == 'ivf':
            quantizer = faiss.IndexFlatL2(self.dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, self.nlist)
        elif self.index_type == 'hnsw':
            self.index = faiss.IndexHNSWFlat(self.dim, self.hnsw_m)
        else:
            raise ValueError(f"Unknown index_type: {self.index_type}")

    def train(self, training_vectors):
        with self.lock:
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                logger.info("Training FAISS index...")
                self.index.train(np.array(training_vectors).astype('float32'))
                logger.info("Training complete.")

    def add(self, vector, metadata=None, uid=None):
        with self.lock:
            vector = np.array(vector).astype('float32').reshape(1, -1)
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                raise RuntimeError("Index needs to be trained before adding vectors.")
            self.index.add(vector)
            idx = len(self.metadata)
            self.metadata.append(metadata)
            if uid is not None:
                self.id_to_idx[uid] = idx
                self.idx_to_id[idx] = uid
            logger.debug(f"Added vector idx={idx}, uid={uid}, metadata={metadata}")

    def add_batch(self, vectors, metadatas=None, uids=None):
        with self.lock:
            vectors = np.array(vectors).astype('float32')
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                raise RuntimeError("Index needs to be trained before adding vectors.")
            self.index.add(vectors)
            start_idx = len(self.metadata)
            n = vectors.shape[0]
            if metadatas:
                self.metadata.extend(metadatas)
            else:
                self.metadata.extend([None] * n)
            if uids:
                for i, uid in enumerate(uids):
                    idx = start_idx + i
                    self.id_to_idx[uid] = idx
                    self.idx_to_id[idx] = uid
            logger.debug(f"Batch added {n} vectors.")

    def search(self, query_vector, top_k=5, return_scores=False):
        with self.lock:
            query_vector = np.array(query_vector).astype('float32').reshape(1, -1)
            D, I = self.index.search(query_vector, top_k)
            results = []
            for dist, idx in zip(D[0], I[0]):
                if idx < len(self.metadata):
                    if return_scores:
                        results.append((self.metadata[idx], float(dist), self.idx_to_id.get(idx)))
                    else:
                        results.append(self.metadata[idx])
            return results

    def search_batch(self, query_vectors, top_k=5, return_scores=False):
        with self.lock:
            query_vectors = np.array(query_vectors).astype('float32')
            D, I = self.index.search(query_vectors, top_k)
            results = []
            for dists, indices in zip(D, I):
                batch_result = []
                for dist, idx in zip(dists, indices):
                    if idx < len(self.metadata):
                        if return_scores:
                            batch_result.append((self.metadata[idx], float(dist), self.idx_to_id.get(idx)))
                        else:
                            batch_result.append(self.metadata[idx])
                results.append(batch_result)
            return results

    def search_with_filter(self, query_vector, top_k=5, filter_fn: Optional[Callable[[Any], bool]] = None, return_scores=False):
        # Get more results to allow filtering
        raw_results = self.search(query_vector, top_k=top_k*4, return_scores=return_scores)
        filtered = []
        for item in raw_results:
            meta = item[0] if return_scores else item
            if filter_fn is None or filter_fn(meta):
                filtered.append(item)
            if len(filtered) >= top_k:
                break
        return filtered

    def get_by_id(self, uid):
        with self.lock:
            idx = self.id_to_idx.get(uid)
            if idx is not None and idx < len(self.metadata):
                return self.metadata[idx]
            return None

    def save(self, index_path, meta_path):
        with self.lock:
            faiss.write_index(self.index, index_path)
            with open(meta_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'id_to_idx': self.id_to_idx,
                    'idx_to_id': self.idx_to_id,
                    'dim': self.dim,
                    'index_type': self.index_type,
                    'nlist': self.nlist,
                    'hnsw_m': self.hnsw_m
                }, f)
            logger.info(f"Saved index to {index_path} and metadata to {meta_path}")

    def load(self, index_path, meta_path):
        with self.lock:
            self.index = faiss.read_index(index_path)
            with open(meta_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.id_to_idx = data['id_to_idx']
                self.idx_to_id = data['idx_to_id']
                self.dim = data['dim']
                self.index_type = data['index_type']
                self.nlist = data['nlist']
                self.hnsw_m = data['hnsw_m']
            logger.info(f"Loaded index from {index_path} and metadata from {meta_path}")

    # FAISS does not support true deletion; this is a workaround
    def mark_deleted(self, uid):
        with self.lock:
            idx = self.id_to_idx.get(uid)
            if idx is not None and idx < len(self.metadata):
                self.metadata[idx] = None
                logger.info(f"Marked uid={uid} as deleted.")

    def update(self, uid, new_vector, new_metadata=None):
        # Not efficient; for demo only: mark old as deleted, add new
        self.mark_deleted(uid)
        self.add(new_vector, metadata=new_metadata, uid=uid)
        logger.info(f"Updated uid={uid}.")

# --- DEMO / TEST ---
def test_advanced_faiss_store():
    logger.info("Testing advanced FAISSVectorStore...")
    dim = 4
    store = FAISSVectorStore(dim=dim, index_type='flat')
    # Add vectors with metadata and IDs
    vectors = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    metadatas = [
        {"label": "A", "type": "alpha"},
        {"label": "B", "type": "beta"},
        {"label": "C", "type": "alpha"},
        {"label": "D", "type": "beta"},
    ]
    uids = ["idA", "idB", "idC", "idD"]
    store.add_batch(vectors, metadatas, uids)
    # Search
    results = store.search([1, 0, 0, 0], top_k=3, return_scores=True)
    print("Search results for [1,0,0,0] (top 3, with scores):", results)
    # Search with filter
    filtered = store.search_with_filter([1, 0, 0, 0], top_k=2, filter_fn=lambda m: m and m["type"] == "alpha", return_scores=True)
    print("Filtered search (type=alpha):", filtered)
    # Get by ID
    print("Get by idC:", store.get_by_id("idC"))
    # Mark deleted and update
    store.mark_deleted("idB")
    print("After deletion, get by idB:", store.get_by_id("idB"))
    store.update("idA", [0.5, 0.5, 0, 0], {"label": "A2", "type": "alpha"})
    print("After update, get by idA:", store.get_by_id("idA"))
    # Save/load
    store.save('faiss_adv.index', 'meta_adv.pkl')
    new_store = FAISSVectorStore(dim=dim)
    new_store.load('faiss_adv.index', 'meta_adv.pkl')
    print("Loaded store, search for [0,1,0,0]:", new_store.search([0,1,0,0], top_k=2, return_scores=True))
    # Batch search
    batch_results = new_store.search_batch([[1,0,0,0],[0,0,1,0]], top_k=2, return_scores=True)
    print("Batch search results:", batch_results)

if __name__ == "__main__":
    test_advanced_faiss_store()