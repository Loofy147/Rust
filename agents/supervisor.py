import threading
import time
import logging

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
        try:
            while self.running:
                for i, (t, agent) in enumerate(self.threads):
                    if not t.is_alive():
                        logging.warning(f"Restarting dead agent: {agent.__class__.__name__}")
                        new_t = threading.Thread(target=agent.run, daemon=True)
                        self.threads[i] = (new_t, agent)
                        new_t.start()
                time.sleep(5)
        except KeyboardInterrupt:
            self.running = False
            logging.info("Supervisor shutting down.")