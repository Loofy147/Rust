from .base import Agent

class DistributionAgent(Agent):
    def process(self, msg):
        # Route based on content, e.g., entity/topic
        if msg["type"] == "processed":
            # For demo, just print or log
            self.logger.info(f"Distributed: {msg['content'][:100]}")
        elif msg["type"] == "search_results":
            self.logger.info(f"Search results: {msg['results']}")