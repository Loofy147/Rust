from advanced_orchestrator.registry import AgentRegistry
import requests

class RetrieverAgent:
    def __init__(self, agent_id, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["retrieval"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        # Retrieve data from a URL or API
        url = task.get('url')
        if url:
            resp = requests.get(url)
            return resp.text
        return None