import time
import logging

class MetricsAgent:
    def __init__(self, interval=10):
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            # Placeholder: aggregate metrics from queues, agents, etc.
            logging.info("[MetricsAgent] System health OK.")
            time.sleep(self.interval)