import time

class SelfOptimizationAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["self_optimization", "monitoring", "scaling"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.last_action = None

    def process(self, task):
        # Task: {"type": "monitor", "metrics": {agent_id: {"load": ..., "errors": ...}}}
        metrics = task.get("metrics", {})
        suggestions = []
        for agent_id, m in metrics.items():
            load = m.get("load", 0)
            errors = m.get("errors", 0)
            # Heuristic: if load > 0.8, suggest scale up; if load < 0.2, suggest scale down
            if load > 0.8:
                suggestions.append({"action": "scale_up", "agent_id": agent_id})
            elif load < 0.2:
                suggestions.append({"action": "scale_down", "agent_id": agent_id})
            # Heuristic: if errors > 5, suggest redeploy
            if errors > 5:
                suggestions.append({"action": "redeploy", "agent_id": agent_id})
        self.last_action = {"timestamp": time.time(), "suggestions": suggestions}
        return self.last_action