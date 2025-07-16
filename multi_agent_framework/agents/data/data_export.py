from agents.base import BaseAgent

class DataExportAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_export']

    def process(self, task):
        data = task.get('data')
        output_path = task.get('output_path', 'prepared_data.csv')
        with open(output_path, 'w') as f:
            f.write(data)
        return {'status': 'exported', 'path': output_path}