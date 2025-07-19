class PlannerAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["planning", "workflow_decomposition"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        # Decompose a generic task into subtasks with required skills
        subtasks = [{
            "id": f"{task['id']}_1",
            "skill": "retrieval",
            "desc": "Retrieve info"
        }, {
            "id": f"{task['id']}_2",
            "skill": "summarization",
            "desc": "Summarize info"
        }]
        assignments = []
        for subtask in subtasks:
            candidates = self.registry.find_by_skill(subtask['skill'])
            if candidates:
                assignments.append((candidates[0], subtask))
        return assignments