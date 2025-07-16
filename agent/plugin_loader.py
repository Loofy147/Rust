import os
from agent.plugins.llm_openai import OpenAILLM
from agent.plugins.kg_sqlalchemy import SQLAlchemyKG
from agent.plugins.vector_chroma import ChromaVectorStore
from agent.metrics import PrintMetrics
from agent.prompt_builder import PromptBuilder

def load_plugins():
    llm_type = os.getenv("LLM_PLUGIN", "openai")
    kg_type = os.getenv("KG_PLUGIN", "sqlalchemy")
    vector_type = os.getenv("VECTOR_PLUGIN", "chroma")
    metrics_type = os.getenv("METRICS_PLUGIN", "print")

    if llm_type == "openai":
        llm = OpenAILLM(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))
    else:
        raise NotImplementedError(f"LLM plugin {llm_type} not implemented")

    if kg_type == "sqlalchemy":
        kg = SQLAlchemyKG(os.getenv("DB_URL", "sqlite:///kg.db"))
    else:
        raise NotImplementedError(f"KG plugin {kg_type} not implemented")

    if vector_type == "chroma":
        vector_store = ChromaVectorStore()
    else:
        raise NotImplementedError(f"Vector plugin {vector_type} not implemented")

    if metrics_type == "print":
        metrics = PrintMetrics()
    else:
        raise NotImplementedError(f"Metrics plugin {metrics_type} not implemented")

    prompt_builder = PromptBuilder()
    return llm, kg, vector_store, metrics, prompt_builder