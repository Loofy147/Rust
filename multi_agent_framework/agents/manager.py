from .base import Agent

class ManagerAgent(Agent):
    def __init__(self, name, inbox, outboxes, config, agents):
        super().__init__(name, inbox, outboxes, config)
        self.agents = agents

    def process(self, msg):
        # Monitor agent states, scale if needed
        for agent in self.agents:
            self.logger.info(f"Agent {agent.name} state: {agent.state}")
        # Example: send health check
        if msg.get("type") == "health_check":
            for agent in self.agents:
                self.send({"type": "ping"}, agent.name)