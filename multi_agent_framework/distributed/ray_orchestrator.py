import ray
import time
import logging

ray.init(ignore_reinit_error=True)


class RayOrchestrator:

    def __init__(self, config, agent_classes):
        self.config = config
        self.agent_classes = agent_classes
        self.agents = {}
        self.logger = logging.getLogger("RayOrchestrator")

    def launch_agents(self):
        for name, agent_class in self.agent_classes.items():
            self.agents[name] = agent_class.remote(name, self.config)
        self.logger.info(f"Launched agents: {list(self.agents.keys())}")

    def send(self, from_agent, to_agent, msg):
        self.agents[from_agent].send.remote(msg, self.agents[to_agent])

    def monitor(self):
        while True:
            for name, agent in self.agents.items():
                state = ray.get(agent.heartbeat.remote())
                self.logger.info(f"Agent {name} state: {state}")
            time.sleep(5)

    def stop(self):
        for agent in self.agents.values():
            agent.stop.remote()
        self.logger.info("All agents stopped.")


if __name__ == "__main__":
    # Example usage
    from agents.summarization import RaySummarizationAgent
    config = {"openai_api_key": "sk-..."}
    agent_classes = {"summarizer": RaySummarizationAgent}
    orchestrator = RayOrchestrator(config, agent_classes)
    orchestrator.launch_agents()
    orchestrator.send("summarizer", "summarizer", {
        "type": "summarize",
        "text": "Ray is a distributed framework."
    })
    orchestrator.monitor()