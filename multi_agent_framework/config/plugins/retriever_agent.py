import requests


class RetrieverAgent:
    def __init__(self, agent_id, registry):
        self.agent_id = agent_id
        self.registry = registry
        self.skills = ["retrieval", "web_fetch"]
        self.registry.register(agent_id, {"skills": self.skills})

    def process(self, task):
        url = task.get("url")
        if url:
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                return {"content": resp.text}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "No URL provided"}
