import queue

class TaskScheduler:
    def __init__(self):
        self.priority_queue = queue.PriorityQueue()
    def add_task(self, priority, task):
        self.priority_queue.put((priority, task))
    def get_task(self):
        if not self.priority_queue.empty():
            return self.priority_queue.get()[1]
        return None