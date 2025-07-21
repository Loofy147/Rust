import unittest
from advanced_orchestrator.workflow import WorkflowEngine

class TestAdvancedWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()

    def test_nested_conditional_workflow(self):
        steps = [
            {'id': 'a'},
            {'id': 'b', 'depends_on': ['a'], 'condition': {
                'and': [
                    {'step': 'a', 'equals': 'success'},
                    {'not': {'step': 'a', 'equals': 'failure'}}
                ]
            }},
        ]
        self.engine.add_workflow('nested_cond1', steps, dag=True)

        completed = ['a']
        memory = {'a': 'success'}
        next_steps = self.engine.next_steps('nested_cond1', completed, memory)
        self.assertEqual(set(next_steps), {'b'})

    def test_error_handling_with_fallback(self):
        steps = [
            {'id': 'a', 'on_failure': 'c'},
            {'id': 'b', 'depends_on': ['a']},
            {'id': 'c'}
        ]
        self.engine.add_workflow('fallback1', steps, dag=True)

        self.engine.record_step_output('fallback1', 'a', 'error', status='failure')
        next_steps = self.engine.next_steps('fallback1', ['a'], {})
        self.assertEqual(set(next_steps), {'c'})

if __name__ == '__main__':
    unittest.main()
