from autonomous_architect.agents.base import AutonomousArchitectAgent, AgentCapability
from autonomous_architect.events import ArchitectureEventType

class PerformanceAgent(AutonomousArchitectAgent):
    def __init__(self, agent_id, codebase_graph):
        super().__init__(agent_id, [AgentCapability.PERFORMANCE_OPTIMIZATION, AgentCapability.TESTING_ORCHESTRATION], codebase_graph)
        self.last_performance = {}
    async def handle_event(self, event):
        if event['type'] == ArchitectureEventType.PERFORMANCE_ALERT:
            await self.optimize_performance(event)
        elif event['type'] == ArchitectureEventType.TEST_RESULT:
            await self.handle_test_result(event)
    async def optimize_performance(self, event):
        metrics = event['payload'].get('metrics', {})
        for k, v in metrics.items():
            prev = self.last_performance.get(k, v)
            if v > prev * 1.2:
                print(f"[{self.agent_id}] Performance regression detected for {k}: {v} > {prev}")
                await self.emit_event({'type': ArchitectureEventType.PERFORMANCE_ALERT, 'payload': {'regression': k, 'value': v}})
            self.last_performance[k] = v
        print(f"[{self.agent_id}] Performance metrics: {metrics}")
    async def handle_test_result(self, event):
        # Suggest optimization if test failed
        if not event['payload'].get('success', True):
            print(f"[{self.agent_id}] Test failed, suggesting optimization.")
            await self.emit_event({'type': ArchitectureEventType.PERFORMANCE_ALERT, 'payload': {'suggestion': 'optimize_code', 'test': event['payload']}})
    async def emit_event(self, event):
        print(f"[{self.agent_id}] Emitting event: {event}")