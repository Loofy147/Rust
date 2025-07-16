import networkx as nx
import threading
from core.event_store import EventStore

class WorkflowEngine:
    def __init__(self, event_store=None):
        self._workflows = {}
        self._lock = threading.Lock()
        self.event_store = event_store or EventStore()
        self._read_model = {}
        self._hitl_approvals = {}  # workflow_id -> set of approved step ids
        self._memory = {}  # workflow_id -> {step_id: output}
        self._feedback_log = {}  # workflow_id -> list of feedback dicts

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
            self._hitl_approvals[workflow_id] = set()
            self._memory[workflow_id] = {}
            self._feedback_log[workflow_id] = []

    def get_workflow(self, workflow_id):
        with self._lock:
            return self._workflows.get(workflow_id)

    def next_steps(self, workflow_id, completed_steps):
        wf = self.get_workflow(workflow_id)
        if isinstance(wf, nx.DiGraph):
            ready = [n for n in wf.nodes if all(dep in completed_steps for dep in wf.predecessors(n)) and n not in completed_steps]
            # Filter out HITL steps not yet approved
            ready = [n for n in ready if not self._is_hitl_step(wf, n) or n in self._hitl_approvals[workflow_id]]
            return ready
        else:
            for step in wf:
                if step['id'] not in completed_steps:
                    if self._is_hitl_step(step) and step['id'] not in self._hitl_approvals[workflow_id]:
                        return []
                    return [step['id']]
            return []

    def approve_hitl_step(self, workflow_id, step_id):
        with self._lock:
            self._hitl_approvals[workflow_id].add(step_id)
            self.event_store.append_event('hitl_approved', {'workflow_id': workflow_id, 'step_id': step_id})

    def record_step_output(self, workflow_id, step_id, output):
        with self._lock:
            self._memory[workflow_id][step_id] = output

    def get_memory(self, workflow_id):
        with self._lock:
            return dict(self._memory[workflow_id])

    def log_feedback(self, workflow_id, step_id, feedback):
        with self._lock:
            self._feedback_log[workflow_id].append({'step_id': step_id, 'feedback': feedback})

    def get_feedback_log(self, workflow_id):
        with self._lock:
            return list(self._feedback_log[workflow_id])

    def _is_hitl_step(self, wf, step):
        # For DAG, wf is nx.DiGraph; for chain, step is dict
        if isinstance(wf, nx.DiGraph):
            return wf.nodes[step].get('hitl', False)
        return step.get('hitl', False)

    def _update_read_model(self, workflow_id):
        self._read_model[workflow_id] = self._workflows[workflow_id]