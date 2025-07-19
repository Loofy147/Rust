from advanced_orchestrator.registry import AgentRegistry


class MemoryAgent:
    def __init__(self, agent_id, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["memory"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.memory = {}

    def process(self, task):
        action = task.get('action')
        key = task.get('key')
        value = task.get('value')
        if action == 'set' and key:
            self.memory[key] = value
            return {"status": "set", "key": key}
        elif action == 'get' and key:
            return {"value": self.memory.get(key)}
        elif action == 'delete' and key:
            self.memory.pop(key, None)
            return {"status": "deleted", "key": key}
        return {"status": "noop"}
