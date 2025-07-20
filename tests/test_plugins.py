from agent.plugins.llm_openai import OpenAILLM
from agent.plugins.kg_sqlalchemy import SQLAlchemyKG
from agent.plugins.vector_chroma import ChromaVectorStore
from agent.metrics import PrintMetrics
import os

def test_llm_plugin():
    plugin = OpenAILLM(api_key="sk-test")
    assert hasattr(plugin, "call")

def test_kg_plugin(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    kg = SQLAlchemyKG(db_url)
    assert hasattr(kg, "query")
    assert hasattr(kg, "store")

def test_vector_plugin():
    vector_store = ChromaVectorStore()
    assert hasattr(vector_store, "add")
    assert hasattr(vector_store, "query")

def test_metrics_plugin():
    metrics = PrintMetrics()
    metrics.emit("test_metric", 1)