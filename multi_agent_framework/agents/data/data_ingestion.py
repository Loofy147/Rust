from agents.base import BaseAgent

class DataIngestionAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_ingestion']

    def process(self, task):
        source = task.get('source')
        # Stub: fetch data from file, URL, or DB
        if source and source.startswith('http'):
            import requests
            data = requests.get(source).text
        elif source and source.endswith('.csv'):
            with open(source, 'r') as f:
                data = f.read()
        else:
            data = 'dummy_data'
        return {'data': data}