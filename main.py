import yaml
from agents.supervisor import SupervisorAgent
from agents.metrics import MetricsAgent
from agents.processor import ProcessorAgent
from agents.task_queue import TaskQueueAgent
from agents.registry import AgentRegistry
from agents.scheduler import TaskScheduler
from plugins.plugin_manager import PluginManager
from plugins.dynamic_loader import DynamicPluginLoader
from storage.base import get_storage_backend
from utils.logging import setup_logging

with open('config.yaml') as f:
    config = yaml.safe_load(f)

setup_logging(config['runtime']['log_level'])

# Initialize registry, scheduler, dynamic plugin loader
agent_registry = AgentRegistry()
task_scheduler = TaskScheduler()
dynamic_plugin_loader = DynamicPluginLoader()

# Initialize storage
storage = get_storage_backend(config['storage'])

# Initialize plugins
plugin_manager = PluginManager(config['plugins'], dynamic_loader=dynamic_plugin_loader)

# Initialize agents
metrics_agent = MetricsAgent(storage=storage)
processor_agent = ProcessorAgent(storage, plugin_manager, config['llm'])
task_queue_agent = TaskQueueAgent(processor_agent=processor_agent, scheduler=task_scheduler)

# Register agents
agent_registry.register('metrics', {'type': 'metrics', 'status': 'ready'})
agent_registry.register('processor', {'type': 'processor', 'status': 'ready'})
agent_registry.register('task_queue', {'type': 'task_queue', 'status': 'ready'})

supervisor = SupervisorAgent([
    metrics_agent,
    processor_agent,
    task_queue_agent
], registry=agent_registry)

if __name__ == "__main__":
    supervisor.run()