from advanced_orchestrator.registry import AgentRegistry
from advanced_orchestrator.workflow import WorkflowEngine
from advanced_orchestrator.event_bus import EventBus
from advanced_orchestrator.monitoring import Monitoring
from advanced_orchestrator.api import app, REGISTRY, WORKFLOW_ENGINE, EVENT_BUS
from advanced_orchestrator.plugin_loader import PluginLoader
from core.event_store import EventStore
import threading
import uvicorn
import time
import yaml
import os

class AdvancedOrchestrator:
    def __init__(self):
        self.event_store = EventStore()
        self.registry = AgentRegistry(event_store=self.event_store)
        self.workflow_engine = WorkflowEngine(event_store=self.event_store)
        self.event_bus = EventBus()
        self.monitoring = Monitoring()
        # Inject dependencies into API
        app.REGISTRY = self.registry
        app.WORKFLOW_ENGINE = self.workflow_engine
        app.EVENT_BUS = self.event_bus
        # Plugin loader
        config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.plugin_loader = PluginLoader(os.path.join(os.path.dirname(__file__), '../config/plugins'), self.registry)
        self.plugin_loader.load_plugins(self.config)
        # Stubs for advanced features
        self.human_in_the_loop_queue = []  # For HITL steps
        self.edge_agents = {}  # For edge/federated agent support
        self.emergent_behavior_log = []  # For emergent behavior analysis

    def start_api(self):
        threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info"), daemon=True).start()

    def monitor_agents(self):
        while True:
            metrics = {}
            for agent_id, agent in self.registry.all().items():
                self.monitoring.update_agent(
                    agent_id,
                    agent['status'],
                    agent['load'],
                    agent['last_heartbeat']
                )
                metrics[agent_id] = {
                    "load": agent['load'],
                    "errors": agent.get('errors', 0)
                }
            # Send metrics to SelfOptimizationAgent if loaded
            if 'self_optimization_agent' in self.plugin_loader.agent_pools:
                result = self.plugin_loader.assign_task(
                    'self_optimization_agent',
                    {"type": "monitor", "metrics": metrics}
                )
                print("[SelfOptimizationAgent Suggestions]", result)
            if 'self_optimization_rl_agent' in self.plugin_loader.agent_pools:
                result_rl = self.plugin_loader.assign_task(
                    'self_optimization_rl_agent',
                    {"type": "monitor", "metrics": metrics}
                )
                print("[SelfOptimizationRLAgent Suggestions]", result_rl)
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