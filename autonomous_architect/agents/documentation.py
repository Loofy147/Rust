import ast
from autonomous_architect.agents.base import AutonomousArchitectAgent, AgentCapability
from autonomous_architect.events import ArchitectureEventType

class DocumentationAgent(AutonomousArchitectAgent):
    def __init__(self, agent_id, codebase_graph):
        super().__init__(agent_id, [AgentCapability.DOCUMENTATION_GENERATION], codebase_graph)
    async def handle_event(self, event):
        if event['type'] == ArchitectureEventType.DOC_UPDATE:
            await self.generate_documentation(event)
    async def generate_documentation(self, event):
        code = event['payload'].get('code', '')
        try:
            tree = ast.parse(code)
            missing_docs = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        missing_docs.append(node.name)
            if missing_docs:
                print(f"[{self.agent_id}] Missing docstrings for: {missing_docs}")
                await self.emit_event({'type': ArchitectureEventType.DOC_UPDATE, 'payload': {'missing_docs': missing_docs}})
            else:
                print(f"[{self.agent_id}] All functions/classes documented.")
        except Exception as e:
            print(f"[{self.agent_id}] AST parse error: {e}")
    async def emit_event(self, event):
        print(f"[{self.agent_id}] Emitting event: {event}")