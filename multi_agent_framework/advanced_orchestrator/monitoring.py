import logging
import time
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Prometheus metrics
api_request_counter = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
api_error_counter = Counter('api_errors_total', 'Total API errors', ['endpoint', 'method'])
agent_task_counter = Counter('agent_tasks_total', 'Total tasks processed by agent', ['agent_id'])
agent_error_counter = Counter('agent_errors_total', 'Total errors by agent', ['agent_id'])
workflow_duration_histogram = Histogram('workflow_duration_seconds', 'Workflow execution duration', ['workflow_id'])

# OpenTelemetry tracing
tracer_provider = TracerProvider()
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

class Monitoring:
    def __init__(self):
        self.logger = logging.getLogger("Monitoring")
        self.agent_status_gauge = Gauge('agent_status', 'Status of agents', ['agent_id', 'status'])
        self.agent_load_gauge = Gauge('agent_load', 'Load of agents', ['agent_id'])
        self.agent_heartbeat_gauge = Gauge('agent_heartbeat', 'Last heartbeat of agents', ['agent_id'])
        start_http_server(8001)

    def update_agent(self, agent_id, status, load, last_heartbeat):
        self.agent_status_gauge.labels(agent_id=agent_id, status=status).set(1)
        self.agent_load_gauge.labels(agent_id=agent_id).set(load)
        self.agent_heartbeat_gauge.labels(agent_id=agent_id).set(last_heartbeat)
        self.logger.info(f"Agent {agent_id} status: {status}, load: {load}, heartbeat: {last_heartbeat}")