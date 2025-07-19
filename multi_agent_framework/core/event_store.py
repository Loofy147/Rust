import threading
import time
from typing import Callable, List, Dict

# For demo: in-memory event log, but can be extended to Postgres/Kafka
class EventStore:
    def __init__(self):
        self._events = []
        self._subscribers = []
        self._lock = threading.Lock()

    def append_event(self, event_type: str, data: dict):
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        with self._lock:
            self._events.append(event)
            for cb in self._subscribers:
                cb(event)

    def get_events(self, event_type: str = None) -> List[Dict]:
        with self._lock:
            if event_type:
                return [e for e in self._events if e['type'] == event_type]
            return list(self._events)

    def subscribe(self, callback: Callable):
        with self._lock:
            self._subscribers.append(callback)
