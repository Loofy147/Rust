import queue
import logging
from agents.ingestion import IngestionAgent
from agents.processing import ProcessingAgent
from agents.distribution import DistributionAgent
from agents.manager import ManagerAgent
from agents.webscraper import WebScraperAgent
from agents.code_generator import CodeGeneratorAgent
from agents.maintenance import MaintenanceAgent
from core.knowledge_graph import KnowledgeGraph
from core.vector_store import VectorStore
from config import CONFIG
import multiprocessing
from fastapi import FastAPI, Request
import uvicorn
import threading

app = FastAPI()

# Global agent references for REST API
AGENTS = {}
QUEUES = {}

@app.post("/submit_task")
async def submit_task(request: Request):
    data = await request.json()
    agent = data.get("agent")
    msg = data.get("msg")
    if agent in QUEUES:
        QUEUES[agent].put(msg)
        return {"status": "submitted", "agent": agent}
    return {"status": "error", "reason": "Unknown agent"}

@app.get("/agent_status")
async def agent_status():
    return {name: agent.state for name, agent in AGENTS.items()}

@app.get("/health")
async def health():
    return {"status": "ok"}

def setup_logging():
    logging.basicConfig(level=getattr(logging, CONFIG["log_level"]))

def launch_agents():
    # Queues
    ingestion_inbox = queue.Queue()
    processing_inbox = queue.Queue()
    distribution_inbox = queue.Queue()
    manager_inbox = queue.Queue()
    webscraper_inbox = queue.Queue()
    codegen_inbox = queue.Queue()
    maintenance_inbox = queue.Queue()

    outboxes = {
        "processing": processing_inbox,
        "distribution": distribution_inbox,
        "manager": manager_inbox,
        "webscraper": webscraper_inbox,
        "codegen": codegen_inbox,
        "maintenance": maintenance_inbox
    }

    kg = KnowledgeGraph()
    vs = VectorStore(dim=CONFIG["vector_dim"])

    ingestion_agent = IngestionAgent("ingestion", ingestion_inbox, outboxes, CONFIG)
    processing_agent = ProcessingAgent("processing", processing_inbox, outboxes, CONFIG, kg, vs)
    distribution_agent = DistributionAgent("distribution", distribution_inbox, outboxes, CONFIG)
    manager_agent = ManagerAgent("manager", manager_inbox, outboxes, CONFIG, [ingestion_agent, processing_agent, distribution_agent])
    webscraper_agent = WebScraperAgent("webscraper", webscraper_inbox, outboxes, CONFIG)
    codegen_agent = CodeGeneratorAgent("codegen", codegen_inbox, outboxes, CONFIG)
    maintenance_agent = MaintenanceAgent("maintenance", maintenance_inbox, outboxes, CONFIG, [ingestion_agent, processing_agent, distribution_agent, webscraper_agent, codegen_agent])

    agents = [ingestion_agent, processing_agent, distribution_agent, manager_agent, webscraper_agent, codegen_agent, maintenance_agent]
    agent_dict = {a.name: a for a in agents}
    queue_dict = {a.name: a.inbox for a in agents}

    for agent in agents:
        agent.start()

    return agent_dict, queue_dict, kg, vs

def main():
    setup_logging()
    agent_dict, queue_dict, kg, vs = launch_agents()
    global AGENTS, QUEUES
    AGENTS = agent_dict
    QUEUES = queue_dict

    # Simulate input
    queue_dict["ingestion"].put({"type": "file", "path": "sample.txt"})
    queue_dict["processing"].put({"type": "query", "content": "What is AI?"})
    queue_dict["webscraper"].put({"type": "scrape", "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"})
    queue_dict["codegen"].put({"type": "codegen", "prompt": "Write a Python function to compute Fibonacci numbers."})
    queue_dict["maintenance"].put({"type": "maintenance"})

    # Start REST API in a separate thread
    api_thread = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info"), daemon=True)
    api_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for agent in agent_dict.values():
            agent.stop()
        for agent in agent_dict.values():
            agent.join()
        kg.save(CONFIG["kg_path"])
        vs.save(CONFIG["vector_index_path"])

if __name__ == "__main__":
    main()