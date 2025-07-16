from advanced_orchestrator.registry import AgentRegistry

class SupervisorAgent:
    def __init__(self, agent_id, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["supervision", "audit", "policy_enforcement"]
        self.registry.register(agent_id, {"skills": self.skills})
        self.audit_log = []

    def process(self, task):
        event = task.get('event')
        if event:
            self.audit_log.append(event)
            # Example: enforce a simple policy
            if event.get('type') == 'error':
                return {"action": "alert", "details": event}
        return {"status": "logged"}