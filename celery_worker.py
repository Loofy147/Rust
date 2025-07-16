import os
from celery import Celery
from agent.plugin_loader import load_plugins
from agent.core import ReasoningAgent

celery_app = Celery(
    "reasoning_agent",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

llm, kg, vector_store, metrics, prompt_builder = load_plugins()
agent = ReasoningAgent(llm, kg, vector_store, metrics, prompt_builder)

@celery_app.task
def process_task_celery(task_id, task_input):
    result = agent.handle_task(task_input)
    return {"task_id": task_id, "result": result}