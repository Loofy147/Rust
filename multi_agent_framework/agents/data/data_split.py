from agents.base import BaseAgent
import pandas as pd
from io import StringIO
from sklearn.model_selection import train_test_split

class DataSplitAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_split']

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        train, test = train_test_split(df, test_size=0.2, random_state=42)
        train, val = train_test_split(train, test_size=0.2, random_state=42)
        return {
            'train': train.to_csv(index=False),
            'val': val.to_csv(index=False),
            'test': test.to_csv(index=False)
        }