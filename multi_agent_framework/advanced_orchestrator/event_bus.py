import threading
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type, callback):
        with self._lock:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type, data):
        with self._lock:
            callbacks = list(self._subscribers[event_type])
        for cb in callbacks:
            cb(event_type, data)