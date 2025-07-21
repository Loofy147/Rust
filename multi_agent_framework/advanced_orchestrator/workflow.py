import networkx as nx
import threading
import time
from core.event_store import EventStore

class WorkflowEngine:
    """
    Advanced workflow engine for DAGs, branching, and conditional logic.
    """

    def __init__(self, event_store=None):
        self._workflows = {}
        self._lock = threading.Lock()
        self.event_store = event_store or EventStore()
        self._read_model = {}
        self._hitl_approvals = {}  # {workflow_id: {step_id}}
        self._memory = {}  # {workflow_id: {step_id: output}}
        self._feedback_log = {}  # {workflow_id: [feedback_dict]}
        self._run_status = {}  # {workflow_id: {step_id: status}}
        self._run_history = {}  # {workflow_id: [{step_id, status, ...}]}

    def add_workflow(self, workflow_id, steps, dag=False):
        """Add a workflow definition (DAG or chain)."""
        with self._lock:
            if dag:
                graph = nx.DiGraph()
                for step in steps:
                    graph.add_node(step['id'], **step)
                for step in steps:
                    for dep in step.get('depends_on', []):
                        graph.add_edge(dep, step['id'])
                self._workflows[workflow_id] = graph
            else:
                self._workflows[workflow_id] = steps
            self.event_store.append_event(
                'workflow_added',
                {'workflow_id': workflow_id, 'steps': steps, 'dag': dag})
            self._update_read_model(workflow_id)
            self._hitl_approvals[workflow_id] = set()
            self._memory[workflow_id] = {}
            self._feedback_log[workflow_id] = []
            self._run_status[workflow_id] = {}
            self._run_history[workflow_id] = []

    def get_workflow(self, workflow_id):
        with self._lock:
            return self._workflows.get(workflow_id)

    def next_steps(self, workflow_id, completed_steps, memory=None):
        """Return next steps ready to run, considering branching/conditions."""
        workflow = self.get_workflow(workflow_id)
        if isinstance(workflow, nx.DiGraph):
            ready = [
                n for n in workflow.nodes
                if all(dep in completed_steps
                       for dep in workflow.predecessors(n)) and
                n not in completed_steps
            ]
            # Filter by HITL and conditions
            ready = [
                n for n in ready
                if not self._is_hitl_step(workflow, n) or
                n in self._hitl_approvals[workflow_id]
            ]
            ready = [
                n for n in ready
                if self._check_conditions(workflow, n, memory)
            ]

            # Handle loops
            for step_id in ready:
                step = workflow.nodes[step_id]
                if "loop" in step:
                    return self._handle_loop(workflow_id, step, memory, completed_steps)

            return ready
        else:
            for step in workflow:
                if step['id'] not in completed_steps:
                    if self._is_hitl_step(
                            workflow, step
                    ) and step['id'] not in self._hitl_approvals[workflow_id]:
                        return []
                    if not self._check_conditions(workflow, step, memory):
                        return []

                    if "loop" in step:
                        return self._handle_loop(workflow_id, step, memory, completed_steps)

                    return [step['id']]
            return []

    def _handle_loop(self, workflow_id, step, memory, completed_steps):
        loop_condition = step["loop"]["condition"]
        loop_steps = step["loop"]["steps"]

        # Check if the loop should continue
        if self._evaluate_condition(loop_condition, memory):
            # Check the status of the inner loop steps
            inner_completed = all(
                s["id"] in completed_steps for s in loop_steps
            )

            if not inner_completed:
                # Find the first step of the loop that is not completed
                for inner_step in loop_steps:
                    if inner_step["id"] not in completed_steps:
                        return [inner_step["id"]]
            else:
                # If all inner steps are completed, reset their status and run the first one
                for inner_step in loop_steps:
                    if inner_step["id"] in self._run_status[workflow_id]:
                        del self._run_status[workflow_id][inner_step["id"]]
                return [loop_steps[0]["id"]]

        # If the loop condition is not met, the loop is finished.
        return []

    def approve_hitl_step(self, workflow_id, step_id):
        with self._lock:
            self._hitl_approvals[workflow_id].add(step_id)
            self.event_store.append_event(
                'hitl_approved',
                {'workflow_id': workflow_id, 'step_id': step_id})

    def record_step_output(self, workflow_id, step_id, output,
                           status='success'):
        """Record step output, status, and add to run history."""
        with self._lock:
            self._memory[workflow_id][step_id] = output
            self._run_status[workflow_id][step_id] = status
            self._run_history[workflow_id].append({
                'step_id': step_id,
                'status': status,
                'output': output,
                'timestamp': time.time()
            })

            if status == 'failure':
                self._handle_failure(workflow_id, step_id)

    def _handle_failure(self, workflow_id, step_id):
        workflow = self.get_workflow(workflow_id)
        step = workflow.nodes[step_id]

        retries = step.get('retries', 0)
        if retries > 0:
            self.retry_step(workflow_id, step_id)
            step['retries'] -= 1
        elif 'on_failure' in step:
            failure_step_id = step['on_failure']
            # Add the failure step to the workflow
            if isinstance(workflow, nx.DiGraph):
                workflow.add_node(failure_step_id, id=failure_step_id)
                workflow.add_edge(step_id, failure_step_id)

    def get_memory(self, workflow_id):
        with self._lock:
            return dict(self._memory[workflow_id])

    def log_feedback(self, workflow_id, step_id, feedback):
        with self._lock:
            self._feedback_log[workflow_id].append({
                'step_id': step_id,
                'feedback': feedback
            })

    def get_feedback_log(self, workflow_id):
        with self._lock:
            return list(self._feedback_log[workflow_id])

    def get_run_status(self, workflow_id):
        """Get current run status for all steps."""
        with self._lock:
            return dict(self._run_status[workflow_id])

    def get_run_history(self, workflow_id):
        """Get full execution history for a workflow run."""
        with self._lock:
            return list(self._run_history[workflow_id])

    def retry_step(self, workflow_id, step_id):
        """Mark a step for retry."""
        with self._lock:
            self._run_status[workflow_id][step_id] = 'retry'

    def set_timeout(self, workflow_id, step_id, timeout_sec):
        """Set a timeout for a step (stub for async/worker support)."""
        pass

    def _is_hitl_step(self, wf, step):
        # For DAG, wf is nx.DiGraph; for chain, step is dict
        if isinstance(wf, nx.DiGraph):
            return wf.nodes[step].get('hitl', False)
        return step.get('hitl', False)

    def _check_conditions(self, wf, step, memory):
        """Check if step should run based on conditions and memory."""
        if isinstance(wf, nx.DiGraph):
            cond = wf.nodes[step].get('condition')
        else:
            cond = step.get('condition')
        if not cond:
            return True

        if memory:
            return self._evaluate_condition(cond, memory)

        return True

    def _evaluate_condition(self, condition, memory):
        if "and" in condition:
            return all(self._evaluate_condition(c, memory) for c in condition["and"])
        if "or" in condition:
            return any(self._evaluate_condition(c, memory) for c in condition["or"])
        if "not" in condition:
            return not self._evaluate_condition(condition["not"], memory)

        step_id = condition.get("step")
        if step_id:
            value = memory.get(step_id)

            if "equals" in condition:
                return value == condition["equals"]
            if "not_equals" in condition:
                return value != condition["not_equals"]
            if "greater_than" in condition:
                return value > condition["greater_than"]
            if "less_than" in condition:
                return value < condition["less_than"]

        return False

    def _update_read_model(self, workflow_id):
        self._read_model[workflow_id] = self._workflows[workflow_id]
