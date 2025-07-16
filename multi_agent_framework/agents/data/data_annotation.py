from agents.base import BaseAgent
import pandas as pd
from io import StringIO

class DataAnnotationAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_annotation']
        self._pending = []  # List of (index, sample)
        self._labels = {}   # index -> label

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        # Find samples needing annotation (no 'label' column or label is NaN)
        if 'label' not in df.columns:
            df['label'] = None
        pending = df[df['label'].isnull()]
        self._pending = list(pending.iterrows())
        # Return samples needing annotation
        return {'pending_samples': pending.to_dict(orient='records'), 'data': raw_data}

    def submit_label(self, index, label):
        self._labels[index] = label
        # In production, update persistent storage or event store
        return {'status': 'labeled', 'index': index, 'label': label}