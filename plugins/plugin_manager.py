import logging
import importlib

class PluginManager:
    def __init__(self, config, dynamic_loader=None):
        self.plugins = {}
        self.dynamic_loader = dynamic_loader
        plugin_configs = config.get('plugins', {})

        for name in plugin_configs.get('enabled', []):
            try:
                plugin_info = plugin_configs.get(name)
                if plugin_info:
                    module_name = plugin_info['module']
                    class_name = plugin_info['class']
                    module = importlib.import_module(module_name)
                    plugin_class = getattr(module, class_name)
                    self.plugins[name] = plugin_class(plugin_info.get('config', {}))
            except (ImportError, AttributeError) as e:
                logging.error(f"Error loading plugin {name}: {e}")

    def run(self, name, *args, **kwargs):
        try:
            if name in self.plugins:
                return self.plugins[name].run(*args, **kwargs)
            if self.dynamic_loader:
                plugin = self.dynamic_loader.get(name)
                if plugin:
                    return plugin.run(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error running plugin {name}: {e}")
        return None

    def load_plugin(self, module_name, class_name):
        try:
            if self.dynamic_loader:
                plugin = self.dynamic_loader.load(module_name, class_name)
                self.plugins[class_name] = plugin
                return plugin
        except Exception as e:
            logging.error(f"Error loading plugin {module_name}.{class_name}: {e}")
        return None

    def unload_plugin(self, class_name):
        try:
            if self.dynamic_loader:
                self.dynamic_loader.unload(class_name)
            if class_name in self.plugins:
                del self.plugins[class_name]
        except Exception as e:
            logging.error(f"Error unloading plugin {class_name}: {e}")