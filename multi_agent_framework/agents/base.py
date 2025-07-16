import threading
import queue
import logging
import time
import traceback
from advanced_orchestrator.monitoring import agent_task_counter, agent_error_counter, tracer

class Agent(threading.Thread):
    def __init__(self, name, inbox, outboxes, config):
        super().__init__(daemon=True)
        self.name = name
        self.inbox = inbox
        self.outboxes = outboxes
        self.config = config
        self.state = "idle"
        self.logger = logging.getLogger(name)
        self.running = True

    def send(self, msg, outbox_name):
        if outbox_name in self.outboxes:
            self.outboxes[outbox_name].put(msg)
            self.logger.info(f"Sent message to {outbox_name}: {msg}")

    def receive(self):
        try:
            msg = self.inbox.get(timeout=1)
            self.logger.info(f"Received message: {msg}")
            return msg
        except queue.Empty:
            return None

    def run(self):
        self.logger.info("Agent started.")
        while self.running:
            msg = self.receive()
            if msg:
                try:
                    self.state = "busy"
                    self.process(msg)
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                finally:
                    self.state = "idle"
            else:
                time.sleep(0.1)

    def process(self, msg):
        with tracer.start_as_current_span(f"agent_{self.name}_process"):
            agent_task_counter.labels(agent_id=self.name).inc()
            start = time.time()
            try:
                result = self._process(msg)
                return result
            except Exception as e:
                agent_error_counter.labels(agent_id=self.name).inc()
                self.log_error(e, msg)
                return {
                    "status": "error",
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "trace": traceback.format_exc()
                }
            finally:
                duration = time.time() - start
                # Optionally, add a duration metric here

    def stop(self):
        self.running = False
        self.logger.info("Agent stopped.")

    def log_error(self, error, task):
        self.logger.error(f"Error in {self.name}: {error}\nTask: {task}\nTrace: {traceback.format_exc()}")