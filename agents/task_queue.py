import queue
import logging
import time

class TaskQueueAgent:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.running = True

    def add_task(self, task):
        self.task_queue.put(task)
        logging.info(f"Task added: {task}")

    def run(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                logging.info(f"Processing task: {task}")
                # TODO: Dispatch to processor or plugin
            except queue.Empty:
                time.sleep(0.5)