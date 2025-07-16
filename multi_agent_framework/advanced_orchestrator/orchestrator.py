from advanced_orchestrator.registry import AgentRegistry
from advanced_orchestrator.workflow import WorkflowEngine
from advanced_orchestrator.event_bus import EventBus
from advanced_orchestrator.monitoring import Monitoring
from advanced_orchestrator.api import app, REGISTRY, WORKFLOW_ENGINE, EVENT_BUS
import threading
import uvicorn
import time

class AdvancedOrchestrator:
    def __init__(self):
        self.registry = AgentRegistry()
        self.workflow_engine = WorkflowEngine()
        self.event_bus = EventBus()
        self.monitoring = Monitoring()
        # Inject dependencies into API
        app.REGISTRY = self.registry
        app.WORKFLOW_ENGINE = self.workflow_engine
        app.EVENT_BUS = self.event_bus

    def start_api(self):
        threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info"), daemon=True).start()

    def monitor_agents(self):
        while True:
            for agent_id, agent in self.registry.all().items():
                self.monitoring.update_agent(
                    agent_id,
                    agent['status'],
                    agent['load'],
                    agent['last_heartbeat']
                )
            time.sleep(5)

    def run(self):
        self.start_api()
        threading.Thread(target=self.monitor_agents, daemon=True).start()
        # Main event loop for orchestrator (e.g., workflow execution, event handling)
        while True:
            time.sleep(1)

if __name__ == "__main__":
    orchestrator = AdvancedOrchestrator()
    orchestrator.run()