import importlib
import logging

class DynamicPluginLoader:
    def __init__(self):
        self.loaded_plugins = {}

    def load(self, module_name, class_name, version=None, dependencies=None):
        if dependencies is None:
            dependencies = []

        # Check for dependencies
        for dep in dependencies:
            if dep not in self.loaded_plugins:
                logging.error(f"Dependency {dep} not found for plugin {class_name}")
                return None

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)

            # Check for version if specified
            if version and hasattr(plugin_class, '__version__') and plugin_class.__version__ != version:
                logging.error(f"Version mismatch for plugin {class_name}. Expected {version}, found {plugin_class.__version__}")
                return None

            self.loaded_plugins[class_name] = plugin_class({})
            return self.loaded_plugins[class_name]
        except ImportError as e:
            logging.error(f"Error importing plugin {module_name}.{class_name}: {e}")
            return None
        except AttributeError as e:
            logging.error(f"Error getting class {class_name} from module {module_name}: {e}")
            return None

    def unload(self, class_name):
        if class_name in self.loaded_plugins:
            del self.loaded_plugins[class_name]

    def get(self, class_name):
        return self.loaded_plugins.get(class_name)