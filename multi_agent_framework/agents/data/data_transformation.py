from agents.base import BaseAgent
import pandas as pd
from io import StringIO

class DataTransformationAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_transformation']

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        # Example: add a feature (length of first column)
        first_col = df.columns[0]
        df['feature_len'] = df[first_col].astype(str).apply(len)
        return {'data': df.to_csv(index=False)}