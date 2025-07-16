from agents.base import BaseAgent
import pandas as pd
from io import StringIO

class DataLabelingAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_labeling']

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        # Example: label as 1 if feature_len > 5
        if 'feature_len' in df.columns:
            df['label'] = (df['feature_len'] > 5).astype(int)
        else:
            df['label'] = 0
        return {'data': df.to_csv(index=False)}