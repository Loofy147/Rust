import queue
import logging
from agents.ingestion import IngestionAgent
from agents.processing import ProcessingAgent
from agents.distribution import DistributionAgent
from agents.manager import ManagerAgent
from core.knowledge_graph import KnowledgeGraph
from core.vector_store import VectorStore
from config import CONFIG

def setup_logging():
    logging.basicConfig(level=getattr(logging, CONFIG["log_level"]))

def main():
    setup_logging()
    # Queues
    ingestion_inbox = queue.Queue()
    processing_inbox = queue.Queue()
    distribution_inbox = queue.Queue()
    manager_inbox = queue.Queue()

    outboxes = {
        "processing": processing_inbox,
        "distribution": distribution_inbox,
        "manager": manager_inbox
    }

    kg = KnowledgeGraph()
    vs = VectorStore(dim=CONFIG["vector_dim"])

    ingestion_agent = IngestionAgent("ingestion", ingestion_inbox, outboxes, CONFIG)
    processing_agent = ProcessingAgent("processing", processing_inbox, outboxes, CONFIG, kg, vs)
    distribution_agent = DistributionAgent("distribution", distribution_inbox, outboxes, CONFIG)
    manager_agent = ManagerAgent("manager", manager_inbox, outboxes, CONFIG, [ingestion_agent, processing_agent, distribution_agent])

    # Start agents
    for agent in [ingestion_agent, processing_agent, distribution_agent, manager_agent]:
        agent.start()

    # Simulate input
    ingestion_inbox.put({"type": "file", "path": "sample.txt"})
    processing_inbox.put({"type": "query", "content": "What is AI?"})
    manager_inbox.put({"type": "health_check"})

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for agent in [ingestion_agent, processing_agent, distribution_agent, manager_agent]:
            agent.stop()
        for agent in [ingestion_agent, processing_agent, distribution_agent, manager_agent]:
            agent.join()
        kg.save(CONFIG["kg_path"])
        vs.save(CONFIG["vector_index_path"])

if __name__ == "__main__":
    main()