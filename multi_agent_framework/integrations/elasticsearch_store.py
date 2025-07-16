from elasticsearch import Elasticsearch

class ElasticsearchStore:
    def __init__(self, host='localhost', port=9200, index='documents'):
        self.es = Elasticsearch([{'host': host, 'port': port}])
        self.index = index
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index)

    def add_document(self, doc_id, body):
        self.es.index(index=self.index, id=doc_id, body=body)

    def search(self, query, size=5):
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content^2", "title"]
                }
            }
        }
        res = self.es.search(index=self.index, body=body, size=size)
        return res['hits']['hits']