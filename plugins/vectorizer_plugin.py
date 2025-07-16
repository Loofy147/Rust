from sentence_transformers import SentenceTransformer
import numpy as np

class VectorizerPlugin:
    def __init__(self, config):
        self.model = SentenceTransformer(config.get('model', 'all-MiniLM-L6-v2'))
    def run(self, text):
        return self.model.encode([text])[0].tolist()