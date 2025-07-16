import threading
import queue
import logging
import time
import traceback

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
        raise NotImplementedError

    def stop(self):
        self.running = False
        self.logger.info("Agent stopped.")

    def log_error(self, error, task):
        self.logger.error(f"Error in {self.name}: {error}\nTask: {task}\nTrace: {traceback.format_exc()}")