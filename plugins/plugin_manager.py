class PluginManager:
    def __init__(self, config, dynamic_loader=None):
        self.plugins = {}
        self.dynamic_loader = dynamic_loader
        for name in config.get('enabled', []):
            if name == 'tokenizer':
                from .tokenizer_plugin import TokenizerPlugin
                self.plugins['tokenizer'] = TokenizerPlugin(config.get('tokenizer', {}))
            if name == 'normalizer':
                from .normalizer_plugin import NormalizerPlugin
                self.plugins['normalizer'] = NormalizerPlugin(config.get('normalizer', {}))
            if name == 'vectorizer':
                from .vectorizer_plugin import VectorizerPlugin
                self.plugins['vectorizer'] = VectorizerPlugin(config.get('vectorizer', {}))
    def run(self, name, *args, **kwargs):
        if name in self.plugins:
            return self.plugins[name].run(*args, **kwargs)
        if self.dynamic_loader:
            plugin = self.dynamic_loader.get(name)
            if plugin:
                return plugin.run(*args, **kwargs)
        return None
    def load_plugin(self, module_name, class_name):
        if self.dynamic_loader:
            plugin = self.dynamic_loader.load(module_name, class_name)
            self.plugins[class_name] = plugin
            return plugin
    def unload_plugin(self, class_name):
        if self.dynamic_loader:
            self.dynamic_loader.unload(class_name)
            if class_name in self.plugins:
                del self.plugins[class_name]