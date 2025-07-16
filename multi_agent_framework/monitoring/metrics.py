from prometheus_client import Counter, Gauge, Histogram, start_http_server

agent_task_counter = Counter('agent_tasks_total', 'Total tasks processed by agent', ['agent_id'])
agent_error_counter = Counter('agent_errors_total', 'Total errors by agent', ['agent_id'])
agent_latency_histogram = Histogram('agent_task_latency_seconds', 'Task processing latency', ['agent_id'])

# Start Prometheus metrics server on port 8002
def start_metrics_server():
    start_http_server(8002)