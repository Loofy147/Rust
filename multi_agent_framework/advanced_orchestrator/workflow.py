import networkx as nx
import threading
from core.event_store import EventStore

class WorkflowEngine:
    def __init__(self, event_store=None):
        self._workflows = {}
        self._lock = threading.Lock()
        self.event_store = event_store or EventStore()
        # CQRS read model stub
        self._read_model = {}

    def add_workflow(self, workflow_id, steps, dag=False):
        with self._lock:
            if dag:
                G = nx.DiGraph()
                for step in steps:
                    G.add_node(step['id'], **step)
                for step in steps:
                    for dep in step.get('depends_on', []):
                        G.add_edge(dep, step['id'])
                self._workflows[workflow_id] = G
            else:
                self._workflows[workflow_id] = steps
            self.event_store.append_event('workflow_added', {'workflow_id': workflow_id, 'steps': steps, 'dag': dag})
            self._update_read_model(workflow_id)

    def get_workflow(self, workflow_id):
        with self._lock:
            return self._workflows.get(workflow_id)

    def next_steps(self, workflow_id, completed_steps):
        wf = self.get_workflow(workflow_id)
        if isinstance(wf, nx.DiGraph):
            ready = [n for n in wf.nodes if all(dep in completed_steps for dep in wf.predecessors(n)) and n not in completed_steps]
            return ready
        else:
            for step in wf:
                if step['id'] not in completed_steps:
                    return [step['id']]
            return []

    def _update_read_model(self, workflow_id):
        # Stub: update CQRS read model
        self._read_model[workflow_id] = self._workflows[workflow_id]