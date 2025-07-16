from celery import Celery, Task
import logging
import time

celery_app = Celery('agents', broker='redis://localhost:6379/0')

class CeleryAgent(Task):
    abstract = True
    name = None
    config = None
    state = "idle"
    logger = logging.getLogger("CeleryAgent")
    last_heartbeat = time.time()

    def run(self, msg):
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