import logging
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Dict, List, Optional

class Task:
    def __init__(self, func: Callable, args: tuple = (), kwargs: dict = None, priority: int = 0, description: str = ""):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.description = description

class GlobalContext:
    def __init__(self, project_goal: str, schema: Optional[dict] = None):
        self.project_goal = project_goal
        self.schema = schema or {}
        self.state = {}
        self.lock = threading.Lock()

    def update(self, key, value):
        with self.lock:
            self.state[key] = value

    def get(self, key):
        with self.lock:
            return self.state.get(key)

class OrchestratorAI:
    def __init__(self, max_workers: int = 4, project_goal: str = "Build a robust, scalable, and intelligent agent system."):
        self.logger = logging.getLogger("OrchestratorAI")
        self.global_context = GlobalContext(project_goal)
        self.task_queue = queue.PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        self.active_futures = []
        self.agent_registry: Dict[str, Any] = {}
        self.supervisor_thread = threading.Thread(target=self.supervise, daemon=True)
        self.supervisor_thread.start()

    def register_agent(self, name: str, agent: Any):
        self.agent_registry[name] = agent
        self.logger.info(f"Registered agent: {name}")

    def submit_task(self, task: Task):
        self.task_queue.put((task.priority, time.time(), task))
        self.logger.info(f"Task submitted: {task.description}")

    def run(self):
        while self.running:
            try:
                _, _, task = self.task_queue.get(timeout=1)
                future = self.executor.submit(self._run_task, task)
                self.active_futures.append(future)
            except queue.Empty:
                continue

    def _run_task(self, task: Task):
        try:
            self.logger.info(f"Running task: {task.description}")
            result = task.func(*task.args, **task.kwargs)
            self.logger.info(f"Task completed: {task.description}")
            return result
        except Exception as e:
            self.logger.error(f"Task failed: {task.description} | Error: {e}")
            return None

    def supervise(self):
        while self.running:
            # Check for completed/faulty tasks
            for future in list(self.active_futures):
                if future.done():
                    self.active_futures.remove(future)
            # Dynamic scaling (example: increase workers if queue is long)
            if self.task_queue.qsize() > len(self.active_futures) and self.executor._max_workers < 16:
                self.executor._max_workers += 1
                self.logger.info(f"Scaling up: max_workers={self.executor._max_workers}")
            time.sleep(2)

    def stop(self):
        self.running = False
        self.executor.shutdown(wait=True)
        self.logger.info("OrchestratorAI stopped.")

    def get_status(self):
        return {
            "active_futures": len(self.active_futures),
            "queue_size": self.task_queue.qsize(),
            "max_workers": self.executor._max_workers,
            "global_context": self.global_context.state,
        }