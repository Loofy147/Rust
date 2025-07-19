import unittest
from advanced_orchestrator.registry import AgentRegistry
from advanced_orchestrator.workflow import WorkflowEngine
from agents.advanced.planner import PlannerAgent
from agents.advanced.retriever import RetrieverAgent

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.registry = AgentRegistry()
        self.workflow = WorkflowEngine()
        self.planner = PlannerAgent('planner1', self.registry)
        self.retriever = RetrieverAgent('retriever1', self.registry)

    def test_workflow_execution(self):
        # Register agents and create a simple workflow
        steps = [
            {'id': 'plan', 'agent': 'planner1'},
            {'id': 'retrieve', 'agent': 'retriever1', 'depends_on': ['plan']}
        ]
        self.workflow.add_workflow('wf1', steps, dag=True)
        completed = []
        # Simulate execution
        for _ in range(2):
            next_steps = self.workflow.next_steps('wf1', completed)
            for step_id in next_steps:
                step = next(s for s in steps if s['id'] == step_id)
                agent = self.registry.get(step['agent'])
                self.assertIsNotNone(agent)
                completed.append(step_id)
        self.assertEqual(set(completed), {'plan', 'retrieve'})

if __name__ == '__main__':
    unittest.main()