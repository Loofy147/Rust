from agents.base import BaseAgent
from agents.data.data_ingestion import DataIngestionAgent
from agents.data.data_cleaning import DataCleaningAgent
from agents.data.data_transformation import DataTransformationAgent
from agents.data.data_labeling import DataLabelingAgent
from agents.data.data_split import DataSplitAgent
from agents.data.data_export import DataExportAgent

class DataPreparationAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['data_preparation']
        self.ingest = DataIngestionAgent(agent_id + '_ingest', registry)
        self.clean = DataCleaningAgent(agent_id + '_clean', registry)
        self.transform = DataTransformationAgent(agent_id + '_transform', registry)
        self.label = DataLabelingAgent(agent_id + '_label', registry)
        self.split = DataSplitAgent(agent_id + '_split', registry)
        self.export = DataExportAgent(agent_id + '_export', registry)

    def process(self, task):
        data = self.ingest.process(task)['data']
        data = self.clean.process({'data': data})['data']
        data = self.transform.process({'data': data})['data']
        data = self.label.process({'data': data})['data']
        splits = self.split.process({'data': data})
        export_results = {}
        for split_name, split_data in splits.items():
            export_results[split_name] = self.export.process({'data': split_data, 'output_path': f'{split_name}_prepared.csv'})
        return export_results