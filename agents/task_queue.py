import queue
import logging
import time

class TaskQueueAgent:
    def __init__(self, processor_agent=None, scheduler=None):
        self.running = True
        self.processor_agent = processor_agent
        self.scheduler = scheduler
        self.tasks = {}  # task_id -> info
        self.task_counter = 0

    def add_task(self, task, priority=10):
        task_id = self.task_counter
        self.task_counter += 1
        task['id'] = task_id
        task['status'] = 'pending'
        task['result'] = None
        self.tasks[task_id] = task
        if self.scheduler:
            self.scheduler.add_task(priority, task)
        else:
            # fallback to FIFO
            if not hasattr(self, 'task_queue'):
                self.task_queue = queue.Queue()
            self.task_queue.put(task)
        logging.info(f"Task added: {task}")
        return task_id

    def get_task_status(self, task_id):
        return self.tasks.get(task_id, {})

    def run(self):
        while self.running:
            try:
                if self.scheduler:
                    task = self.scheduler.get_task()
                else:
                    task = self.task_queue.get(timeout=1)
                if not task:
                    time.sleep(0.5)
                    continue
                task['status'] = 'processing'
                logging.info(f"Processing task: {task}")
                if task.get('type') == 'process' and self.processor_agent:
                    result = self.processor_agent.process_task(task)
                    task['result'] = result
                    task['status'] = 'done'
                else:
                    task['status'] = 'failed'
                    logging.warning(f"Unknown task type or no processor: {task}")
            except queue.Empty:
                time.sleep(0.5)