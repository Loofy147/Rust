from agents.base import BaseAgent
import pandas as pd
from io import StringIO

class DataValidationAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_validation']

    def process(self, task):
        raw_data = task.get('data')
        df = pd.read_csv(StringIO(raw_data))
        report = {}
        # Schema
        report['columns'] = list(df.columns)
        report['dtypes'] = df.dtypes.astype(str).to_dict()
        # Stats
        report['stats'] = df.describe(include='all').to_dict()
        # Nulls
        report['nulls'] = df.isnull().sum().to_dict()
        # Outliers (simple: z-score > 3)
        outliers = {}
        for col in df.select_dtypes(include='number').columns:
            z = (df[col] - df[col].mean()) / df[col].std()
            outliers[col] = int((z.abs() > 3).sum())
        report['outliers'] = outliers
        # Return report and pass data through
        return {'validation_report': report, 'data': raw_data}