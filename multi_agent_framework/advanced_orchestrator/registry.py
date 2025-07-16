import threading
import time

class AgentRegistry:
    def __init__(self):
        self._agents = {}
        self._lock = threading.Lock()

    def register(self, agent_id, info):
        with self._lock:
            self._agents[agent_id] = {
                'info': info,
                'last_heartbeat': time.time(),
                'status': 'idle',
                'skills': info.get('skills', []),
                'load': 0
            }

    def unregister(self, agent_id):
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]

    def heartbeat(self, agent_id, status=None, load=None):
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id]['last_heartbeat'] = time.time()
                if status:
                    self._agents[agent_id]['status'] = status
                if load is not None:
                    self._agents[agent_id]['load'] = load

    def get(self, agent_id):
        with self._lock:
            return self._agents.get(agent_id)

    def all(self):
        with self._lock:
            return dict(self._agents)

    def find_by_skill(self, skill):
        with self._lock:
            return [aid for aid, a in self._agents.items() if skill in a['skills']]