class TokenizerPlugin:
    def __init__(self, config):
        self.config = config

    def run(self, text):
        # Simple whitespace tokenizer
        return text.split()