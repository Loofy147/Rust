from agents.base import BaseAgent
import pandas as pd
from io import StringIO

class DataCleaningAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_cleaning']

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        df = df.drop_duplicates()
        df = df.fillna(method='ffill').fillna(method='bfill')
        return {'data': df.to_csv(index=False)}