import unittest
import yaml
from plugins.plugin_manager import PluginManager
from plugins.dynamic_loader import DynamicPluginLoader

class TestPlugins(unittest.TestCase):
    def setUp(self):
        with open('config.yaml') as f:
            self.config = yaml.safe_load(f)
        self.dynamic_loader = DynamicPluginLoader()
        self.plugin_manager = PluginManager(self.config, self.dynamic_loader)

    def test_sentiment_analyzer_plugin(self):
        sentiment = self.plugin_manager.run('sentiment_analyzer', 'I love this!')
        self.assertIsNotNone(sentiment)
        self.assertGreater(sentiment.polarity, 0)

    def test_dynamic_plugin_loading(self):
        # The sentiment_analyzer is loaded by default, let's run it
        sentiment = self.plugin_manager.run('sentiment_analyzer', 'I love this!')
        self.assertIsNotNone(sentiment)
        self.assertGreater(sentiment.polarity, 0)

        # Unload the sentiment analyzer plugin
        self.plugin_manager.unload_plugin('sentiment_analyzer')
        sentiment = self.plugin_manager.run('sentiment_analyzer', 'I love this!')
        self.assertIsNone(sentiment)

        # Load the sentiment analyzer plugin dynamically
        self.plugin_manager.load_plugin('plugins.sentiment_analyzer_plugin', 'SentimentAnalyzerPlugin')
        sentiment = self.plugin_manager.run('SentimentAnalyzerPlugin', 'I love this!')
        self.assertIsNotNone(sentiment)
        self.assertGreater(sentiment.polarity, 0)

if __name__ == '__main__':
    unittest.main()
