from .base import Agent

class ProcessingAgent(Agent):
    def __init__(self, name, inbox, outboxes, config, kg, vector_store):
        super().__init__(name, inbox, outboxes, config)
        self.kg = kg
        self.vector_store = vector_store

    def process(self, msg):
        if msg["type"] == "text":
            text = msg["content"]
            self.kg.extract_from_text(text)
            self.vector_store.add_texts([text])
            self.send({"type": "processed", "content": text}, "distribution")
        elif msg["type"] == "query":
            results = self.vector_store.search(msg["content"])
            self.send({"type": "search_results", "results": results}, "distribution")