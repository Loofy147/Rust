import logging
import time
from prometheus_client import Counter, Gauge, start_http_server

class Monitoring:
    def __init__(self):
        self.logger = logging.getLogger("Monitoring")
        self.agent_status_gauge = Gauge('agent_status', 'Status of agents', ['agent_id', 'status'])
        self.agent_load_gauge = Gauge('agent_load', 'Load of agents', ['agent_id'])
        self.agent_heartbeat_gauge = Gauge('agent_heartbeat', 'Last heartbeat of agents', ['agent_id'])
        start_http_server(8001)

    def update_agent(self, agent_id, status, load, last_heartbeat):
        self.agent_status_gauge.labels(agent_id=agent_id, status=status).set(1)
        self.agent_load_gauge.labels(agent_id=agent_id).set(load)
        self.agent_heartbeat_gauge.labels(agent_id=agent_id).set(last_heartbeat)
        self.logger.info(f"Agent {agent_id} status: {status}, load: {load}, heartbeat: {last_heartbeat}")