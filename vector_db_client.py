import pinecone
import os

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_ENV = os.environ.get('PINECONE_ENV')
PINECONE_INDEX = os.environ.get('PINECONE_INDEX', 'agentsys-index')

class PineconeClient:
    def __init__(self, dim=384):
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        if PINECONE_INDEX not in pinecone.list_indexes():
            pinecone.create_index(PINECONE_INDEX, dimension=dim)
        self.index = pinecone.Index(PINECONE_INDEX)

    def upsert(self, vec_id, vector, payload=None):
        meta = payload if isinstance(payload, dict) else {"text": str(payload)}
        self.index.upsert([(vec_id, vector, meta)])

    def search(self, vector, k=5):
        res = self.index.query(vector=[vector], top_k=k, include_metadata=True)
        return res['matches']