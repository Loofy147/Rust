import random
import time

class MonitoringAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["monitoring"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        # In a real system, this would query a metrics backend like Prometheus
        # For this demo, we generate mock metrics
        agents_to_monitor = ["planner1", "retriever1", "summarizer1"]
        metrics = {}
        for agent in agents_to_monitor:
            metrics[agent] = {
                "load": random.uniform(0.1, 0.95),
                "errors": random.randint(0, 7),
                "latency_ms": random.randint(50, 500),
            }
        return {"timestamp": time.time(), "metrics": metrics}
