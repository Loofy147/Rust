import os
from celery import Celery
from agent.plugin_loader import load_plugins
from agent.core import ReasoningAgent

if os.getenv("OTEL_ENABLED", "0") == "1":
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    trace.set_tracer_provider(TracerProvider())
    span_processor = BatchSpanProcessor(OTLPSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)

celery_app = Celery(
    "reasoning_agent",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

if os.getenv("OTEL_ENABLED", "0") == "1":
    CeleryInstrumentor().instrument()

llm, kg, vector_store, metrics, prompt_builder = load_plugins()
agent = ReasoningAgent(llm, kg, vector_store, metrics, prompt_builder)

@celery_app.task
def process_task_celery(task_id, task_input):
    result = agent.handle_task(task_input)
    return {"task_id": task_id, "result": result}