import unittest
from advanced_orchestrator.workflow import WorkflowEngine

class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()

    def test_chain_workflow(self):
        steps = [
            {'id': 'a'},
            {'id': 'b'},
            {'id': 'c'}
        ]
        self.engine.add_workflow('chain1', steps, dag=False)
        wf = self.engine.get_workflow('chain1')
        self.assertEqual(len(wf), 3)
        completed = []
        self.assertEqual(self.engine.next_steps('chain1', completed), ['a'])
        completed.append('a')
        self.assertEqual(self.engine.next_steps('chain1', completed), ['b'])
        completed.append('b')
        self.assertEqual(self.engine.next_steps('chain1', completed), ['c'])
        completed.append('c')
        self.assertEqual(self.engine.next_steps('chain1', completed), [])

    def test_dag_workflow(self):
        steps = [
            {'id': 'a'},
            {'id': 'b', 'depends_on': ['a']},
            {'id': 'c', 'depends_on': ['a']},
            {'id': 'd', 'depends_on': ['b', 'c']}
        ]
        self.engine.add_workflow('dag1', steps, dag=True)
        completed = []
        self.assertEqual(set(self.engine.next_steps('dag1', completed)), {'a'})
        completed.append('a')
        self.assertEqual(set(self.engine.next_steps('dag1', completed)), {'b', 'c'})
        completed.extend(['b', 'c'])
        self.assertEqual(set(self.engine.next_steps('dag1', completed)), {'d'})
        completed.append('d')
        self.assertEqual(self.engine.next_steps('dag1', completed), [])

if __name__ == '__main__':
    unittest.main()