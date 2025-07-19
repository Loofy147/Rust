import unittest
from advanced_orchestrator.registry import AgentRegistry
import time

class TestAgentRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = AgentRegistry()

    def test_register_and_get(self):
        self.registry.register('agent1', {'skills': ['test']})
        agent = self.registry.get('agent1')
        self.assertIsNotNone(agent)
        self.assertIn('test', agent['skills'])

    def test_unregister(self):
        self.registry.register('agent2', {'skills': []})
        self.registry.unregister('agent2')
        self.assertIsNone(self.registry.get('agent2'))

    def test_heartbeat(self):
        self.registry.register('agent3', {'skills': []})
        before = self.registry.get('agent3')['last_heartbeat']
        time.sleep(0.01)
        self.registry.heartbeat('agent3', status='busy', load=2)
        after = self.registry.get('agent3')['last_heartbeat']
        self.assertGreater(after, before)
        self.assertEqual(self.registry.get('agent3')['status'], 'busy')
        self.assertEqual(self.registry.get('agent3')['load'], 2)

    def test_find_by_skill(self):
        self.registry.register('agent4', {'skills': ['foo']})
        self.registry.register('agent5', {'skills': ['bar']})
        found = self.registry.find_by_skill('foo')
        self.assertIn('agent4', found)
        self.assertNotIn('agent5', found)

if __name__ == '__main__':
    unittest.main()