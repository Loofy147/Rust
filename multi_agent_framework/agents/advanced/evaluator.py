from advanced_orchestrator.registry import AgentRegistry

class EvaluatorAgent:
    def __init__(self, agent_id, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["evaluation"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        # Evaluate the output (e.g., quality, correctness)
        output = task.get('output')
        if output:
            # Simple heuristic: length check
            score = min(len(output) / 100, 1.0)
            return {"score": score, "feedback": "OK" if score > 0.5 else "Too short"}
        return {"score": 0, "feedback": "No output"}