class AgentRegistry:
    def __init__(self):
        self.agents = {}
    def register(self, name, info):
        self.agents[name] = info
    def get(self, name):
        return self.agents.get(name)
    def all(self):
        return self.agents