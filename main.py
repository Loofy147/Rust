import yaml
from agents.supervisor import SupervisorAgent
from agents.metrics import MetricsAgent
from agents.processor import ProcessorAgent
from plugins.plugin_manager import PluginManager
from storage.base import get_storage_backend
from utils.logging import setup_logging

with open('config.yaml') as f:
    config = yaml.safe_load(f)

setup_logging(config['runtime']['log_level'])

# Initialize storage
storage = get_storage_backend(config['storage'])

# Initialize plugins
plugin_manager = PluginManager(config['plugins'])

# Initialize agents
metrics_agent = MetricsAgent()
processor_agent = ProcessorAgent(storage, plugin_manager, config['llm'])
supervisor = SupervisorAgent([
    metrics_agent,
    processor_agent
])

if __name__ == "__main__":
    supervisor.run()