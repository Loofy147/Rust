from advanced_orchestrator.registry import AgentRegistry

class PlannerAgent:
    def __init__(self, agent_id, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["planning", "workflow_decomposition"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        # Decompose task into subtasks and assign to agents with matching skills
        subtasks = self.decompose(task)
        assignments = []
        for subtask in subtasks:
            candidates = self.registry.find_by_skill(subtask['skill'])
            if candidates:
                assignments.append((candidates[0], subtask))
        return assignments

    def decompose(self, task):
        # Example: break down a generic task into subtasks with required skills
        # In practice, use LLMs or rules
        return [
            {"id": f"{task['id']}_1", "skill": "retrieval", "desc": "Retrieve info"},
            {"id": f"{task['id']}_2", "skill": "summarization", "desc": "Summarize info"}
        ]