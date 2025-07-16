import ray
import time
import logging

@ray.remote
class RayAgent:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.state = "idle"
        self.logger = logging.getLogger(name)
        self.running = True
        self.last_heartbeat = time.time()

    def send(self, msg, agent_handle):
        agent_handle.receive.remote(msg)
        self.logger.info(f"Sent message to {agent_handle}: {msg}")

    def receive(self, msg):
        self.logger.info(f"Received message: {msg}")
        self.state = "busy"
        try:
            self.process(msg)
        except Exception as e:
            self.logger.error(f"Error: {e}")
        self.state = "idle"

    def process(self, msg):
        raise NotImplementedError

    def heartbeat(self):
        self.last_heartbeat = time.time()
        return self.state

    def stop(self):
        self.running = False
        self.logger.info("Agent stopped.")