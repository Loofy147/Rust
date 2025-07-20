import re
from autonomous_architect.agents.base import AutonomousArchitectAgent, AgentCapability
from autonomous_architect.events import ArchitectureEventType

class SecurityAgent(AutonomousArchitectAgent):
    def __init__(self, agent_id, codebase_graph):
        super().__init__(agent_id, [AgentCapability.SECURITY_AUDIT], codebase_graph)
    async def handle_event(self, event):
        if event['type'] == ArchitectureEventType.SECURITY_ALERT:
            await self.audit_security(event)
    async def audit_security(self, event):
        code = event['payload'].get('code', '')
        # Simple regex for insecure function usage
        if re.search(r'\beval\b', code):
            print(f"[{self.agent_id}] Insecure usage of 'eval' detected!")
            await self.emit_event({'type': ArchitectureEventType.SECURITY_ALERT, 'payload': {'issue': 'eval_usage'}})
        # TODO: Add more vulnerability patterns
    async def emit_event(self, event):
        print(f"[{self.agent_id}] Emitting event: {event}")