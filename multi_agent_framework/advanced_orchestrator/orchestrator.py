from advanced_orchestrator.registry import AgentRegistry
from advanced_orchestrator.workflow import WorkflowEngine
from advanced_orchestrator.event_bus import EventBus
from advanced_orchestrator.monitoring import Monitoring
from advanced_orchestrator.api import app
from advanced_orchestrator.plugin_loader import PluginLoader
from core.event_store import EventStore
import threading
import uvicorn
import time
import yaml
import os
from agents.advanced.llm_reasoning import LLMReasoningAgent
from agents.advanced.retriever import RetrieverAgent

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
        app.ORCHESTRATOR = self
        # Plugin loader
        config_path = os.path.join(os.path.dirname(__file__),
                                   '../config/config.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.plugin_loader = PluginLoader(
            os.path.join(os.path.dirname(__file__), '../config/plugins'),
            self.registry)
        self.plugin_loader.load_plugins(self.config)
        # Stubs for advanced features
        self.human_in_the_loop_queue = []  # For HITL steps
        self.edge_agents = {}  # For edge/federated agent support
        self.emergent_behavior_log = []  # For emergent behavior analysis
        self.llm_agent = LLMReasoningAgent('llm_reasoning1', self.registry)
        self.retriever_agent = RetrieverAgent('retriever1', self.registry)

    def start_api(self):
        threading.Thread(target=lambda: uvicorn.run(
            app, host="0.0.0.0", port=8000, log_level="info"),
            daemon=True).start()

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

    def automated_reasoning_pipeline(self, workflow_id, question,
                                     feedback=None):
        try:
            # Step 1: Retrieve context
            retrieval = self.retriever_agent.process({'query': question})
            if retrieval.get('status') == 'error':
                self.event_bus.publish(
                    'error', {'workflow_id': workflow_id, 'step': 'retrieval',
                              'error': retrieval})
                self.workflow_engine.log_feedback(
                    workflow_id, 'retrieval',
                    {'type': 'error', 'error': retrieval})
                return retrieval
            context = retrieval['context']
            # Step 2: LLM reasoning
            llm_result = self.llm_agent.process(
                {'question': question, 'context': context,
                 'feedback': feedback})
            if llm_result.get('status') == 'error':
                self.event_bus.publish(
                    'error',
                    {'workflow_id': workflow_id, 'step': 'llm_reasoning',
                     'error': llm_result})
                self.workflow_engine.log_feedback(
                    workflow_id, 'llm_reasoning',
                    {'type': 'error', 'error': llm_result})
                return llm_result
            self.workflow_engine.record_step_output(
                workflow_id, 'retrieval', retrieval)
            self.workflow_engine.record_step_output(
                workflow_id, 'llm_reasoning', llm_result)
            # Step 3: Feedback/clarification loop
            if llm_result['needs_clarification']:
                print("[LLM] Needs clarification: "
                      f"{llm_result['needs_clarification']}")
                # Escalate to HITL for clarification
                self.human_in_the_loop_queue.append({
                    'workflow_id': workflow_id,
                    'step': 'llm_reasoning',
                    'question': llm_result['needs_clarification'],
                    'context': context
                })
                self.workflow_engine.log_feedback(
                    workflow_id, 'llm_reasoning',
                    {'type': 'clarification',
                     'message': llm_result['needs_clarification']})
                return None
            # Step 4: HITL QA before production
            self.human_in_the_loop_queue.append({
                'workflow_id': workflow_id,
                'step': 'qa',
                'llm_output': llm_result,
                'context': context
            })
            self.workflow_engine.log_feedback(
                workflow_id, 'llm_reasoning',
                {'type': 'output', 'message': llm_result})
            print("[Orchestrator] Output ready for HITL QA: "
                  f"{llm_result['answer']}")
            return llm_result
        except Exception as e:
            import traceback
            error_info = {
                'status': 'error',
                'error_type': type(e).__name__,
                'message': str(e),
                'trace': traceback.format_exc()
            }
            self.event_bus.publish(
                'error', {'workflow_id': workflow_id, 'step': 'orchestrator',
                          'error': error_info})
            self.workflow_engine.log_feedback(
                workflow_id, 'orchestrator',
                {'type': 'error', 'error': error_info})
            return error_info

    def run(self):
        threading.Thread(target=self.monitor_agents, daemon=True).start()
        # Main event loop for orchestrator
        while True:
            time.sleep(1)


if __name__ == "__main__":
    orchestrator = AdvancedOrchestrator()
    orchestrator.start_api()
    orchestrator.run()
