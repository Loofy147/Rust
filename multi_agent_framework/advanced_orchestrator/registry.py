import threading
import time
from core.event_store import EventStore

class AgentRegistry:

    def __init__(self, event_store=None, federated_peers=None):
        self._agents = {}
        self._lock = threading.Lock()
        self.event_store = event_store or EventStore()
        # List of peer URLs or clients
        self.federated_peers = federated_peers or []

    def register(self, agent_id, info):
        with self._lock:
            self._agents[agent_id] = {
                'info': info,
                'last_heartbeat': time.time(),
                'status': 'idle',
                'skills': info.get('skills', []),
                'load': 0
            }
            self.event_store.append_event(
                'agent_registered',
                {'agent_id': agent_id, 'info': info})
            self._sync_to_peers('register', agent_id, info)

    def unregister(self, agent_id):
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self.event_store.append_event('agent_unregistered',
                                              {'agent_id': agent_id})
                self._sync_to_peers('unregister', agent_id)

    def heartbeat(self, agent_id, status=None, load=None):
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id]['last_heartbeat'] = time.time()
                if status:
                    self._agents[agent_id]['status'] = status
                if load is not None:
                    self._agents[agent_id]['load'] = load
                self.event_store.append_event(
                    'agent_heartbeat',
                    {'agent_id': agent_id, 'status': status, 'load': load})

    def get(self, agent_id):
        with self._lock:
            return self._agents.get(agent_id)

    def all(self):
        with self._lock:
            return dict(self._agents)

    def find_by_skill(self, skill):
        with self._lock:
            return [
                aid for aid, a in self._agents.items()
                if skill in a['skills']
            ]

    def register_edge_agent(self, agent_id, info, edge_location):
        with self._lock:
            self._agents[agent_id] = {
                'info': info,
                'last_heartbeat': time.time(),
                'status': 'idle',
                'skills': info.get('skills', []),
                'load': 0,
                'edge_location': edge_location
            }
            self.event_store.append_event(
                'edge_agent_registered',
                {'agent_id': agent_id, 'info': info,
                 'edge_location': edge_location})
            self._sync_to_peers('register_edge', agent_id, info)

    def find_edge_agents(self, location=None):
        with self._lock:
            return [
                aid for aid, a in self._agents.items()
                if 'edge_location' in a and
                (location is None or a['edge_location'] == location)
            ]

    def _sync_to_peers(self, action, agent_id, info=None):
        # Stub for syncing with etcd/Consul or federated registry API
        pass
