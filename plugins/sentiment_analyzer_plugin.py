from textblob import TextBlob

class SentimentAnalyzerPlugin:
    __version__ = "0.1.0"

    def __init__(self, config):
        pass

    def run(self, text):
        return TextBlob(text).sentiment
