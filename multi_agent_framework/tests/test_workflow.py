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

    def test_conditional_workflow(self):
        steps = [
            {'id': 'a'},
            {'id': 'b', 'depends_on': ['a'], 'condition': {'step': 'a', 'equals': 'success'}},
            {'id': 'c', 'depends_on': ['a'], 'condition': {'step': 'a', 'equals': 'failure'}},
        ]
        self.engine.add_workflow('cond1', steps, dag=True)

        # Test case 1: 'a' succeeds
        completed = ['a']
        memory = {'a': 'success'}
        next_steps = self.engine.next_steps('cond1', completed, memory)
        self.assertEqual(set(next_steps), {'b'})

        # Test case 2: 'a' fails
        memory = {'a': 'failure'}
        next_steps = self.engine.next_steps('cond1', completed, memory)
        self.assertEqual(set(next_steps), {'c'})

    def test_looping_workflow(self):
        steps = [
            {'id': 'a', 'loop': {'condition': {'step': 'counter', 'less_than': 3}, 'steps': [{'id': 'b'}, {'id': 'c'}]}},
            {'id': 'd', 'depends_on': ['a']}
        ]
        self.engine.add_workflow('loop1', steps, dag=True)

        completed = []
        memory = {'counter': 0}

        # Iteration 1
        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['b'])
        completed.append('b')
        memory['b'] = 'success'

        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['c'])
        completed.append('c')
        memory['c'] = 'success'
        memory['counter'] = 1

        # Iteration 2
        # Since all steps in the loop are completed, the loop should restart
        completed = []
        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['b'])
        completed.append('b')
        memory['b'] = 'success'

        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['c'])
        completed.append('c')
        memory['c'] = 'success'
        memory['counter'] = 2

        # Iteration 3
        completed = []
        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['b'])
        completed.append('b')
        memory['b'] = 'success'

        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(next_steps, ['c'])
        completed.append('c')
        memory['c'] = 'success'
        memory['counter'] = 3

        # After loop
        completed = ['a']
        next_steps = self.engine.next_steps('loop1', completed, memory)
        self.assertEqual(set(next_steps), {'d'})


    def test_error_handling_workflow(self):
        steps = [
            {'id': 'a', 'retries': 1},
            {'id': 'b', 'depends_on': ['a']},
        ]
        self.engine.add_workflow('error1', steps, dag=True)

        # Test retry
        self.engine.record_step_output('error1', 'a', 'error', status='failure')
        self.assertEqual(self.engine.get_run_status('error1')['a'], 'retry')

        # Test no more retries
        self.engine.record_step_output('error1', 'a', 'error', status='failure')
        self.assertEqual(self.engine.get_run_status('error1')['a'], 'failure')


if __name__ == '__main__':
    unittest.main()