import time
import logging

class MetricsAgent:
    def __init__(self, interval=10, storage=None, agents=None):
        self.interval = interval
        self.running = True
        self.storage = storage
        self.agents = agents or []

    def run(self):
        while self.running:
            # Aggregate metrics from queues, agents, etc.
            healths = {a.__class__.__name__: getattr(a, 'heartbeat', None) for a in self.agents}
            if self.storage and hasattr(self.storage, 'data'):
                vector_count = len(self.storage.data)
                logging.info(f"[MetricsAgent] Vectors stored: {vector_count}")
            logging.info(f"[MetricsAgent] Agent health: {healths}")
            time.sleep(self.interval)