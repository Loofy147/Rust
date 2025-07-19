import os
import pytest
from faiss_vector_store import FAISSVectorStore

def test_add_and_search():
    store = FAISSVectorStore(dim=3)
    store.add([1, 0, 0], metadata={"label": "A"}, uid="a")
    store.add([0, 1, 0], metadata={"label": "B"}, uid="b")
    results = store.search([1, 0, 0], top_k=2)
    assert any(meta and meta.get("label") == "A" for meta in results)

def test_batch_add():
    store = FAISSVectorStore(dim=3)
    vectors = [[1,0,0],[0,1,0],[0,0,1]]
    metadatas = [{"label": "A"}, {"label": "B"}, {"label": "C"}]
    uids = ["a","b","c"]
    store.add_batch(vectors, metadatas, uids)
    results = store.search([0,1,0], top_k=2)
    assert any(meta and meta.get("label") == "B" for meta in results)

def test_save_and_load(tmp_path):
    store = FAISSVectorStore(dim=3)
    store.add([1,0,0], metadata={"label": "A"}, uid="a")
    index_path = tmp_path / "faiss.index"
    meta_path = tmp_path / "meta.pkl"
    store.save(str(index_path), str(meta_path))
    new_store = FAISSVectorStore(dim=3)
    new_store.load(str(index_path), str(meta_path))
    results = new_store.search([1,0,0], top_k=1)
    assert any(meta and meta.get("label") == "A" for meta in results)

def test_metadata_filtering():
    store = FAISSVectorStore(dim=3)
    store.add([1,0,0], metadata={"label": "A", "type": "alpha"})
    store.add([0,1,0], metadata={"label": "B", "type": "beta"})
    def filter_fn(meta):
        return meta and meta.get("type") == "alpha"
    results = store.search_with_filter([1,0,0], top_k=2, filter_fn=filter_fn)
    assert all(meta and meta.get("type") == "alpha" for meta in results)