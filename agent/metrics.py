from agent.interfaces import MetricsPlugin

class PrintMetrics(MetricsPlugin):
    def emit(self, metric_name: str, value, tags: dict = None):
        print(f"METRIC {metric_name}: {value} | tags={tags}")