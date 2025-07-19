class Monitoring:
    """System monitoring for agent performance and health."""
    def __init__(self):
        self.agent_metrics = {}
        self.system_metrics = {}
    def update_agent_metrics(self, agent_id, metrics):
        self.agent_metrics[agent_id] = metrics
    def update_system_metrics(self, metrics):
        self.system_metrics.update(metrics)
    def get_agent_metrics(self, agent_id):
        return self.agent_metrics.get(agent_id, {})
    def get_system_metrics(self):
        return self.system_metrics