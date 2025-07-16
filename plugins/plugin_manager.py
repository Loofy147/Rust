class PluginManager:
    def __init__(self, config):
        self.plugins = {}
        for name in config.get('enabled', []):
            if name == 'tokenizer':
                from .tokenizer_plugin import TokenizerPlugin
                self.plugins['tokenizer'] = TokenizerPlugin(config.get('tokenizer', {}))

    def run(self, name, *args, **kwargs):
        if name in self.plugins:
            return self.plugins[name].run(*args, **kwargs)
        return None