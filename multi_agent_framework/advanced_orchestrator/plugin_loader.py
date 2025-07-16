import importlib.util
import os
import threading

class AgentPool:
    def __init__(self, agent_class, pool_size, registry):
        self.instances = [agent_class(f"{agent_class.__name__}_{i}", registry) for i in range(pool_size)]
        self.lock = threading.Lock()
        self.next_idx = 0

    def get_next(self):
        with self.lock:
            agent = self.instances[self.next_idx]
            self.next_idx = (self.next_idx + 1) % len(self.instances)
            return agent

    def get_least_loaded(self):
        with self.lock:
            return min(self.instances, key=lambda a: a.registry.get(a.agent_id)['load'])

class PluginLoader:
    def __init__(self, plugins_dir, registry):
        self.plugins_dir = plugins_dir
        self.registry = registry
        self.agent_pools = {}

    def load_plugins(self, config):
        for plugin in config.get('plugins', []):
            path = os.path.join(self.plugins_dir, os.path.basename(plugin['path']))
            spec = importlib.util.spec_from_file_location(plugin['name'], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            agent_class = getattr(mod, [c for c in dir(mod) if c.endswith('Agent')][0])
            pool_size = plugin.get('pool_size', 1)
            self.agent_pools[plugin['name']] = AgentPool(agent_class, pool_size, self.registry)

    def assign_task(self, plugin_name, task, strategy='round_robin'):
        pool = self.agent_pools[plugin_name]
        if strategy == 'least_loaded':
            agent = pool.get_least_loaded()
        else:
            agent = pool.get_next()
        return agent.process(task)