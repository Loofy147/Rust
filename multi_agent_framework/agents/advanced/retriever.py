from agents.base import BaseAgent

class RetrieverAgent(BaseAgent):
    def __init__(self, agent_id, registry):
        super().__init__(agent_id, registry)
        self.skills = ['retrieval']
        # In production, connect to FAISS/Elastic/Pinecone
        self.documents = [
            {'id': 1, 'text': 'Domain knowledge about X.'},
            {'id': 2, 'text': 'More info about Y.'},
            {'id': 3, 'text': 'Details on Z.'}
        ]

    def _process(self, task):
        query = task.get('query')
        # For demo: return all docs containing a keyword from query
        results = [doc for doc in self.documents if any(word in doc['text'].lower() for word in query.lower().split())]
        if not results:
            results = self.documents[:1]
        context = '\n'.join([doc['text'] for doc in results])
        return {'context': context, 'docs': results}