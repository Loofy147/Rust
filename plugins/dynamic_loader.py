import importlib

class DynamicPluginLoader:
    def __init__(self):
        self.loaded_plugins = {}
    def load(self, module_name, class_name):
        module = importlib.import_module(module_name)
        plugin_class = getattr(module, class_name)
        self.loaded_plugins[class_name] = plugin_class({})
        return self.loaded_plugins[class_name]
    def unload(self, class_name):
        if class_name in self.loaded_plugins:
            del self.loaded_plugins[class_name]
    def get(self, class_name):
        return self.loaded_plugins.get(class_name)