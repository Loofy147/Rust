class PluginManager:
    def __init__(self, config):
        self.plugins = {}
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
        return None