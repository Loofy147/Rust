class NormalizerPlugin:
    def __init__(self, config):
        self.config = config

    def run(self, text):
        return text.lower().strip()