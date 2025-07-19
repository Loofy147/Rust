from .base import Agent
import os

class IngestionAgent(Agent):
    def process(self, msg):
        # msg: {"type": "file", "path": ...} or {"type": "api", "url": ...}
        if msg["type"] == "file":
            with open(msg["path"], "r") as f:
                text = f.read()
            # Simple chunking
            chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
            for chunk in chunks:
                self.send({"type": "text", "content": chunk}, "processing")
        elif msg["type"] == "api":
            import requests
            resp = requests.get(msg["url"])
            self.send({"type": "text", "content": resp.text}, "processing")