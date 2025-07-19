class EvaluatorAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["evaluation", "scoring"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        output = task.get("output")
        if output:
            score = min(len(output) / 100, 1.0)
            return {
                "score": score,
                "feedback": "OK" if score > 0.5 else "Too short"
            }
        return {"score": 0, "feedback": "No output"}
