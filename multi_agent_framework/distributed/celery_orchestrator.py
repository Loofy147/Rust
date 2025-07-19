import logging
import time


class CeleryOrchestrator:

    def __init__(self, agent_tasks):
        self.agent_tasks = agent_tasks
        self.logger = logging.getLogger("CeleryOrchestrator")

    def send(self, agent_name, msg):
        task = self.agent_tasks[agent_name]
        task.apply_async(args=[msg])
        self.logger.info(f"Sent task to {agent_name}: {msg}")

    def monitor(self):
        # In production, use Flower or custom health checks
        while True:
            self.logger.info(
                "Celery agents running. Monitor with Flower or logs.")
            time.sleep(10)


if __name__ == "__main__":
    from agents.summarization import celery_summarization_task
    agent_tasks = {"summarizer": celery_summarization_task}
    orchestrator = CeleryOrchestrator(agent_tasks)
    orchestrator.send("summarizer", {
        "type": "summarize",
        "text": "Celery is a distributed task queue."
    })
    orchestrator.monitor()