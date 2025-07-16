import queue
import logging
import time

class TaskQueueAgent:
    def __init__(self, processor_agent=None):
        self.task_queue = queue.Queue()
        self.running = True
        self.processor_agent = processor_agent

    def add_task(self, task):
        self.task_queue.put(task)
        logging.info(f"Task added: {task}")

    def run(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                logging.info(f"Processing task: {task}")
                # Type-based routing
                if task.get('type') == 'process' and self.processor_agent:
                    self.processor_agent.process_task(task)
                else:
                    logging.warning(f"Unknown task type or no processor: {task}")
            except queue.Empty:
                time.sleep(0.5)