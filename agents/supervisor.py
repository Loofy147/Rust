import threading
import time
import logging
import signal
from utils.heartbeat import Heartbeat

class SupervisorAgent:
    def __init__(self, agents):
        self.agents = agents
        self.threads = []
        self.running = True

    def run(self):
        for agent in self.agents:
            t = threading.Thread(target=agent.run, daemon=True)
            self.threads.append((t, agent))
            t.start()
        self.heartbeats = [Heartbeat() for _ in self.agents]
        def shutdown_handler(signum, frame):
            self.running = False
            logging.info("Supervisor received shutdown signal.")
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        try:
            while self.running:
                for i, (t, agent) in enumerate(self.threads):
                    if hasattr(agent, 'heartbeat'):
                        self.heartbeats[i].beat()
                    if not t.is_alive() or not self.heartbeats[i].is_alive():
                        logging.warning(f"Restarting dead or unresponsive agent: {agent.__class__.__name__}")
                        new_t = threading.Thread(target=agent.run, daemon=True)
                        self.threads[i] = (new_t, agent)
                        self.heartbeats[i] = Heartbeat()
                        new_t.start()
                time.sleep(5)
        except Exception as e:
            self.running = False
            logging.info(f"Supervisor shutting down: {e}")